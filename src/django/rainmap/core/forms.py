from django.forms import ModelForm, ChoiceField, BooleanField, \
    CharField, IntegerField, ValidationError
from django.contrib.auth.models import User
from core.models import Scan

import NmapOptions

from IPy import IP

import re

DEFAULT_SCAN_OPTIONS = "-sS -PE -PS443 -PA80 -PP -sV -O -sC -T4 -v"


class UserForm(ModelForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class ScanForm(ModelForm):

    class Meta:
        model = Scan
        fields = ['name', 'targets', 'schedule_date']

    opts = NmapOptions.NmapOptions()

    ### UI Elements

    # host discovery
    sn = BooleanField(required=False,
            label=u'Ping',
            help_text=u'disable port scanning')

    Pn = BooleanField(required=False,
            label=u'Skip discovery / assume online',
            help_text=u'treat all hosts as online')

    PS = BooleanField(required=False,
            label=u'TCP SYN')

    PA = BooleanField(required=False,
            label=u'TCP ACK')

    PU = BooleanField(required=False,
            label=u'UDP')

    PY = BooleanField(required=False,
            label=u'SCTP')

    traceroute = BooleanField(required=False,
            label=u'Trace the route',
            help_text=u'Trace hop path to each host')

    # scan techniques
    sS = BooleanField(required=False,
            label=u'TCP SYN Scan')

    sU = BooleanField(required=False,
            label=u'UDP Scan')

    # port specification
    p = CharField(required=False,
            label=u'Port range(s)',
            help_text=u'Only scan the specified ports')

    F = BooleanField(required=False,
            label=u'Fast mode',
            help_text=u'Only scan the top 100 ports')

    top_ports = IntegerField(required=False, min_value=0, max_value=65525,
            label=u'Most popular',
            help_text=u'Only the top most popular')

    # service/version detection

    sV = BooleanField(required=False,
            label=u'Detect remote services/versions',
            help_text=u'Determine service/version info')

    # script scan

    sC = BooleanField(required=False,
            label=u'Scan with the default scripts',
            help_text=u'Run the default NSE scripts')

    # os detection

    O = BooleanField(required=False,
            label=u'Detect the Operating System',
            help_text=u'Enable operating system detection')

    # timing

    T = ChoiceField(
            label=u'Scanning speed',
            choices=[(3, u'normal'), (4, u'aggressive'), (5, u'insane')])

    # output

    v = BooleanField(required=False,
            label=u'Verbose')

    def _isHostname(self, entry):
        '''Check if we have something that can be a hostname as defined by RFCs
        952 and 1123. To note, underscores are not allowed, though Windows
        systems may sometimes use them. We consider them invalid here.
        Hostnames must be qualified - generally this means we require a TLD.

        >>> _isHostname('--packet-trace')
        False
        >>> _isHostname('128.189.9.0')
        False
        >>> _isHostname('12345')
        False
        >>> _isHostname('127.o.o.1')
        False
        >>> _isHostname('www-scanme.nmap.org')
        True
        >>> _isHostname('127.example.com')
        True
        '''

        if len(entry) > 255:
            return False # "too long to be a hostname"
        elif not re.search("\.[a-z]{2,}$", entry, re.I):
            return False # "not a qualified hostname"
        if entry.endswith("."):
            entry = entry[:-1]
        invalid = re.compile("[^a-z\d-]", re.IGNORECASE)
        return all(
            (label and len(label) <= 63
             and not label.startswith("-") and not label.endswith("-")
             and not invalid.search(label))
            for label in entry.split("."))

    def _isIPRange(self, entry):
        '''Check if an IP range has been specified. No checking is made to see
        if this range includes non-public IPs, only that octets are valid.
        '''
        octets = entry.split(".")
        if len(octets) == 4:
            for octet in octets:
                parts = octet.split("-")
                if len(parts) == 2:
                    try:
                        start, end = int(parts[0]), int(parts[1])
                        if not 0 <= start < end <= 255:
                            return False # numbers out of order
                    except:
                        return False # Parse error (range must be numeric)
                elif len(parts) == 1:
                    try:
                        if not 0 <= int(parts[0]) <= 255:
                            return False # IP octets take values between 0-255
                    except:
                        return False # Parse error (range must be numeric)
                else:
                    return False # too many parts for this to be a range
        else:
            return False # too many octets to be an IP

        # all checks passed, must be a valid IP range address
        return True

    def clean_targets(self):
        '''Validate that the targets passed to the scan match the formats that
        Nmap knows how to handle. We currently only list problematic entries in
        the error message(s) and it's up to the user to fix these issues.
        '''

        data = self.cleaned_data['targets'].strip()
        entries = re.split("[\s,]+", data)
        # track errors so that we can inform users of all of them at once
        errlist = []
        for ent in entries:
            try:
                ip = IP(ent)
                if ip.version() != 4 or ip.iptype() != 'PUBLIC':
                    errlist.append(u"'%s' not a public IPv4 address" % ent)
            except ValueError:
                if not self._isIPRange(ent) and not self._isHostname(ent):
                    errlist.append(u"'%s' neither an IP range nor a qualified \
                        hostname." % ent)

        if errlist:
            raise ValidationError(errlist)

        return " ".join(entries)

    def clean_p(self):
        '''Validate that the specified ports follow our given subset of
        options, such as ##,##,###-###,##-###,##
        '''

        data = self.cleaned_data['p']
        if not data:
            return data # empty, nothing to check here

        # track errors so that we can inform users of all of them at once
        errlist = []

        chunks = data.split(",")
        for chunk in chunks:
            try:
                portlist = chunk.split("-")
                num_ports = len(portlist)
                if num_ports < 1 or num_ports > 2:
                    errlist.append(u"%s: specify range as 'start - end'" %
                        chunk)
                elif num_ports == 1 and int(portlist[0]) > 65535:
                    errlist.append(u"%s: ports to be scanned must be between \
                        0 and 65535 inclusive")
                elif num_ports == 2:
                    start, end = int(portlist[0]), int(portlist[1])
                    if start > end:
                        errlist.append(u"%s: the starting port should be \
                            lower than the ending port." % chunk)
                    if start < 0 or end > 65535:
                        errlist.append(u"%s: ports to be scanned must be \
                            between 0 and 65535 inclusive" % chunk)
            except ValueError:
                # values below 0 also get 'trapped' here
                errlist.append(u"%s: not a valid port specification" % chunk)

        if errlist:
            raise ValidationError(errlist)

        return data

    def __init__(self, owner, *args, **kwargs):
        self.owner = owner
        super(ScanForm, self).__init__(*args, **kwargs)

        if 'instance' in kwargs:
            self.opts.parse_string(kwargs['instance'].command)
        else:
            self.opts.parse_string(DEFAULT_SCAN_OPTIONS)

        self.fields['sn'].initial = self.opts['-sn']
        self.fields['Pn'].initial = self.opts['-Pn']

        if self.opts['-PS'] != None:
            self.fields['PS'].initial = True

        if self.opts['-PA'] != None:
            self.fields['PA'].initial = True

        if self.opts['-PU'] != None:
            self.fields['PU'].initial = True

        if self.opts['-PY'] != None:
            self.fields['PY'].initial = True

        self.fields['traceroute'].initial = self.opts['--traceroute']
        self.fields['sS'].initial = self.opts['-sS']
        self.fields['sU'].initial = self.opts['-sU']
        self.fields['p'].initial = self.opts['-p']
        self.fields['F'].initial = self.opts['-F']
        self.fields['top_ports'].initial = self.opts['--top-ports']
        self.fields['sV'].initial = self.opts['-sV']
        self.fields['sC'].initial = self.opts['-sC']
        self.fields['O'].initial = self.opts['-O']
        self.fields['T'].initial = self.opts['-T']
        self.fields['v'].initial = self.opts['-v']

    def save(self, commit=True):
        self.opts['-sn'] = self.cleaned_data['sn']
        self.opts['-Pn'] = self.cleaned_data['Pn']

        if self.cleaned_data['PS']:
            self.opts['-PS'] = ''
        else:
            self.opts['-PS'] = None

        if self.cleaned_data['PA']:
            self.opts['-PA'] = ''
        else:
            self.opts['-PA'] = None

        if self.cleaned_data['PU']:
            self.opts['-PU'] = ''
        else:
            self.opts['-PU'] = None

        if self.cleaned_data['PY']:
            self.opts['-PY'] = ''
        else:
            self.opts['-PY'] = None

        self.opts['--traceroute'] = self.cleaned_data['traceroute']
        self.opts['-sS'] = self.cleaned_data['sS']
        self.opts['-sU'] = self.cleaned_data['sU']

        # CharFields can be empty, but that means None to us
        ports = self.cleaned_data['p']
        if ports:
            self.opts['-p'] = ports
        else:
            self.opts['-p'] = None

        self.opts['-F'] = self.cleaned_data['F']
        if self.cleaned_data['top_ports']:
            self.opts['--top-ports'] = str(self.cleaned_data['top_ports'])
        else:
            self.opts['--top-ports'] = None
        self.opts['-sV'] = self.cleaned_data['sV']
        self.opts['-sC'] = self.cleaned_data['sC']
        self.opts['-O'] = self.cleaned_data['O']
        self.opts['-T'] = self.cleaned_data['T']
        self.opts['-v'] = self.cleaned_data['v']

        # save model, use the parsed command string
        model = super(ScanForm, self).save(commit=False)
        model.command = self.opts.render_string()

        if commit:
            model.save()

        return model
