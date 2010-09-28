import os
import re

from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from rainmap import settings
from rainq import tasks

from core.models import UserProfile, Scan, ScanResult
from core.forms import UserForm, ScanForm

_no_scan_err_ = u"Hmm, there's no such scan associated with your account."

# matching against characters Windows restricts in file names, and slashes
bads = re.compile('/|\\\|\?|\%|\*|\:|;|\||\"|\<|\>')


def _get_scan(request, scan_id):
    try:
        return Scan.objects.get(id=scan_id, owner=request.user)
    except ObjectDoesNotExist:
        return None


def _paginate(request, objects):
    paginator = Paginator(objects, 10)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        object_list = paginator.page(page)
    except (EmptyPage, InvalidPage):
        object_list = paginator.page(paginator.num_pages)

    return object_list


def index(request):
    if request.user.is_authenticated():
        results = ScanResult.objects.filter(for_scan__owner=request.user)
        result_list = _paginate(request, results)
        return render_to_response('core/dashboard.html',
            {'result_list': result_list},
            context_instance=RequestContext(request))
    else:
        return render_to_response('core/guestview.html',
            context_instance=RequestContext(request))


@login_required(redirect_field_name='next')
def profile(request, template='core/profile.html'):
    up = get_object_or_404(UserProfile, for_user=request.user.id)
    form = UserForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        messages.info(request, u'Your changes have been saved.')

    return render_to_response(template,
        {'profile': up,
         'profile_form': form},
         context_instance=RequestContext(request))


@login_required(redirect_field_name='next')
def scan_list(request, template='core/scan_list.html'):
    scans = request.user.scan_set.all()
    scan_list = _paginate(request, scans)

    return render_to_response(template,
        {'scan_list': scan_list},
        context_instance=RequestContext(request))


@login_required(redirect_field_name='next')
def scan_view(request, scan_id, template='core/scan_view.html'):
    requested_scan = _get_scan(request, scan_id)
    if requested_scan:
        results = requested_scan.scanresult_set.all()
        result_list = _paginate(request, results)
        return render_to_response(template,
            {'scan': requested_scan,
             'result_list': result_list},
            context_instance=RequestContext(request))
    else:
        messages.error(request, _no_scan_err_)
        return redirect('core_scan_list')


@login_required(redirect_field_name='next')
def scan_edit(request, scan_id, template='core/scan_edit.html'):
    requested_scan = _get_scan(request, scan_id)
    if requested_scan:
        form = ScanForm(request.user, request.POST or None,
            instance=requested_scan)

        if form.is_valid():
            form.save()
            messages.info(request, u'Your changes have been saved.')

        else:
            return render_to_response(template,
                {'scan_form': form},
                context_instance=RequestContext(request))
    else:
        messages.error(request, _no_scan_err_)

    return redirect('core_scan_list')


@login_required(redirect_field_name='next')
def scan_copy(request, scan_id, template='core/scan_list.html'):
    requested_scan = _get_scan(request, scan_id)
    if requested_scan:
        # create a new scan, keeping selected elements from the original
        new_scan = Scan(
            owner=request.user,
            name=requested_scan.name,
            command=requested_scan.command,
            targets=requested_scan.targets)
        new_scan.save()
        messages.info(request, u'Scan duplicated.')
    else:
        messages.error(request, _no_scan_err_)

    return redirect('core_scan_list')


@login_required(redirect_field_name='next')
def scan_delete(request, scan_id, template='core/scan_list.html'):
    requested_scan = _get_scan(request, scan_id)
    if requested_scan:
        requested_scan.delete()
        asset_path = os.path.abspath(os.path.join(settings.OUTPUT_ROOT,
            str(request.user.id), str(scan_id)))
        tasks.purge_data.delay(asset_path, request.user.id)
        messages.info(request, u'Scan deleted.')
    else:
        messages.error(request, _no_scan_err_)

    return redirect('core_scan_list')


@login_required(redirect_field_name='next')
def scan_new(request, template='core/scan_new.html'):
    form = ScanForm(request.user, request.POST or None)
    if form.is_valid():
        f = form.save(commit=False)
        f.owner = request.user
        f.save()
        messages.info(request, u'Scan created.')
        return redirect('core_scan_list')

    else:
        return render_to_response(template,
            {'scan_form': form},
            context_instance=RequestContext(request))


@login_required(redirect_field_name='next')
def scan_run(request, scan_id, template='core/scan_list.html'):
    next = request.META.get('HTTP_REFERER', None) or 'core_scan_list'
    requested_scan = _get_scan(request, scan_id)
    if requested_scan:
        result = ScanResult(for_scan=requested_scan)
        result.started_on = datetime.now()
        result.save()
        # sanitize output file name
        name_base = "%s_%s" % (requested_scan.name, str(result.started_on))
        while bads.search(name_base):
            name_base = name_base.replace(bads.search(name_base).group(), "-")

        name_base = name_base.replace(" ", "_").strip()
        rel_dir = os.path.join(str(requested_scan.owner.id),
            str(requested_scan.id))

        # create folders, as needed
        if not os.path.isdir(os.path.join(settings.OUTPUT_ROOT, rel_dir)):
            os.makedirs(os.path.join(settings.OUTPUT_ROOT, rel_dir))
        workdir = os.path.join(settings.OUTPUT_ROOT, rel_dir)
        cmd = "--reason --osscan-guess --webxml -oA %s %s %s".strip() % (
            name_base, requested_scan.command, requested_scan.targets)
        tasks.run_scan.delay(name_base, workdir, scan_id, request.user.id,
            result.id, cmd)
        messages.info(request, u'Your scan is queued and will be run shortly.')

    else:
        messages.error(request, _no_scan_err_)

    return redirect(next)


@login_required(redirect_field_name='next')
def result_view(request, result_id, template='core/result_view.html'):
    referer = request.META.get('HTTP_REFERER', None) or reverse('index')
    try:
        r = ScanResult.objects.get(id=result_id, for_scan__owner=request.user)
        view = request.GET.get('view', None)
        # user-specified type; check if the requested format is available
        if r.output and view:
            if view in ['html', 'xml', 'nmap', 'gnmap']:
                name, ext = os.path.splitext(r.output)
                ret = os.path.join(settings.OUTPUT_URL,
                    str(r.for_scan.owner.id), str(r.for_scan.id),
                    name + "." + view)
                return redirect(ret)
            else:
                messages.error(request, u"No such format. Your results are \
                    available as HTML, XML, and plaintext only.")
                return redirect(referer)
        else: # view in iframe
            if r.output:
                resloc = os.path.join(settings.OUTPUT_URL,
                    str(r.for_scan.owner.id), str(r.for_scan.id), r.output)
            else:
                resloc = None
            return render_to_response(template,
                {'result': r,
                 'resloc': resloc,
                 'referer': referer},
                context_instance=RequestContext(request))
    except ObjectDoesNotExist:
        messages.error(request, u"No such result. Either the scan has not yet \
            completed, or the requested result has been deleted already.")
        return redirect(referer)


@login_required(redirect_field_name='next')
def result_delete(request, result_id, template='core/result_delete.html'):
    next = request.META.get('HTTP_REFERER', None) or reverse('index')
    if next.find(reverse('core_result_view', args=[result_id])) > 0:
        next = reverse('index')
    try:
        sr = ScanResult.objects.get(id=result_id, for_scan__owner=request.user)
        sr.delete()
        if sr.output:
            asset_path = os.path.abspath(os.path.join(settings.OUTPUT_ROOT,
                str(sr.for_scan.owner.id), str(sr.for_scan.id),
                os.path.splitext(sr.output)[0]))
            tasks.purge_data.delay(asset_path, request.user.id)
        messages.info(request, u"Result deleted.")
    except ObjectDoesNotExist:
        messages.error(request, u"No such result. Has the scan completed? \
            Or perhaps it's been deleted already.")

    return redirect(next)
