import shutil
import subprocess
import re
from datetime import datetime
from os import chdir, devnull, makedirs, remove
from os.path import abspath, normpath, normcase, join, isdir, isfile

import celery.log
from celery.decorators import task

from django.contrib.sites.models import Site
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from rainmap import settings
from core.models import Scan, ScanResult

# matching against characters Windows restricts in file names, and slashes
bads = re.compile('/|\\\|\?|\%|\*|\:|;|\||\"|\<|\>')


@task(ignore_result=True)
def run_scan(scan_id):
    scan = Scan.objects.get(id=scan_id)
    scan_result = ScanResult(for_scan=scan)
    scan_result.run_on = datetime.now()
    logger = celery.log.LoggingProxy(celery.log.get_default_logger())
    # sanitize output file name
    name_base = "%s_%s" % (scan.name, str(scan_result.run_on))
    while bads.search(name_base):
        name_base = name_base.replace(bads.search(name_base).group(), "-")

    name_base = name_base.replace(" ", "_").strip()
    rel_dir = join(str(scan.owner.id), str(scan.id))

    # create folders, as needed
    if not isdir(join(settings.OUTPUT_ROOT, rel_dir)):
        makedirs(join(settings.OUTPUT_ROOT, rel_dir))
    chdir(join(settings.OUTPUT_ROOT, rel_dir))
    cmd = "--reason --osscan-guess --webxml -oX %s.xml %s %s".strip() % (
        name_base, scan.command, scan.targets)
    logger.write("BEGIN Scan %d | User %d\ncmd: %s" % (scan.id, scan.owner.id,
        cmd))
    status_nmap = subprocess.call(["nmap"] + cmd.split(), stdout=open(devnull))
    logger.write("END Scan %d | User %d\nstatus: %d" % (scan.id, scan.owner.id,
        status_nmap))

    scan_result.finished_ok = (status_nmap == 0)
    # try to save output. even for errors, we might see what happened
    if isfile(join(settings.OUTPUT_ROOT, rel_dir, name_base + ".xml")):
        logger.write("XSLT Scan %d | User %d" % (scan.id, scan.owner.id))
        status_xslt = subprocess.call(["xsltproc", name_base + ".xml", "-o",
            name_base + ".html"])
        if status_xslt == 0:
            scan_result.output = join(rel_dir, name_base + ".html")
        else:
            scan_result.output = join(rel_dir, name_base + ".xml")
    else:
        scan_result.output = None
        scan_result.finished_ok = False # well, no output *is* an error

    scan_result.save()

    if scan.owner.userprofile.mail_results_all or (
        scan.owner.userprofile.mail_results_err and not
            scan_result.finished_ok):

        _email_dispatch.delay(scan_result.id,
            scan.owner.userprofile.mail_results_all)


@task(ignore_result=True)
def purge_data(owner_id, scan_id):
    logger = celery.log.LoggingProxy(celery.log.get_default_logger())
    logger.write("PURGE Scan %d | User %d" % (scan_id, owner_id))
    data_loc = abspath(join(settings.OUTPUT_ROOT, str(owner_id), str(scan_id)))
    shutil.rmtree(data_loc, False, _error_handler)


@task(ignore_result=True)
def purge_result(result_output):
    logger = celery.log.LoggingProxy(celery.log.get_default_logger())
    logger.write("PURGE Result at %s" % result_output)
    try:
        remove(abspath(join(settings.OUTPUT_ROOT, result_output)))
    except:
        pass


def _error_handler(function, path, excinfo):
    mail_admins("SERVER ERROR", "%s\n%s\n%s\n%s" % (func, path, excinfo[:2]))


@task(ignore_result=True)
def _email_dispatch(result_id, send_always):

    sr = ScanResult.objects.get(id=result_id)

    if sr.output:
        link = 'http://%s%s' % (Site.objects.get_current().domain,
            reverse('core_result_view', args=[result_id]))
    else:
        link = None

    profile_link = 'http://%s%s' % (Site.objects.get_current().domain,
        reverse('user_profile'))

    ctx_dict = {'link': link, 'scan_name': sr.for_scan.name,
        'profile_link': profile_link}

    if sr.finished_ok and send_always:
        subj = render_to_string('core/email_results_subject_success.txt',
            ctx_dict)
        body = render_to_string('core/email_results_success.txt', ctx_dict)
    else:
        subj = render_to_string('core/email_results_subject_error.txt',
            ctx_dict)
        body = render_to_string('core/email_results_error.txt', ctx_dict)

    subj = ''.join(subj.splitlines())

    sr.for_scan.owner.email_user(subj, body, 'scanbot@rainmap.org')
