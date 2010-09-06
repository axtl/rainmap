from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


class UserProfile(models.Model):
    """User Profiles store additional user information.

    For the User model, please refer to django.contrib.auth.models.User

    for_user -- the User object that owns this profile
    cr_rem -- credits remaining until the next rollover
    """
    for_user = models.OneToOneField(User)
    cr_rem = models.IntegerField("Credits Remaining", default=1000)
    mail_results_all = models.BooleanField("Email When a Scan Finishes",
        default=True)
    mail_results_err = models.BooleanField("Only Send Email On Errors",
        default=True)

    def __unicode__(self):
        return u"Profile for " + self.for_user.username


def callback_register_profile(sender, instance, **kw):
    profile, new = UserProfile.objects.get_or_create(for_user=instance)

post_save.connect(callback_register_profile, sender=User)


class Scan(models.Model):
    """Encompasses the necessary information to perform a scan.

    owner -- the user to whom this scan belongs.
    name -- a descriptive way to refer to the scan.
    command -- the command Nmap will run when scanning (may be blank).
    targets -- the list of machines to scan (required).
    output -- path to the resulting XML file for the scan.
    """
    owner = models.ForeignKey(User)
    name = models.CharField(max_length=200, verbose_name=u'Profile name',
        help_text=u"Something to remember this profile by.")
    command = models.TextField(blank=True, null=True)
    targets = models.TextField(verbose_name=u'Target(s)',
        help_text=u'Specify targets to scan by hostname, IP range, or in CIDR '
        'form. Separate multiple entries with spaces or new lines.')
    schedule_date = models.DateTimeField(blank=True, null=True)
    schedule_interval = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ('-id', )

    def __unicode__(self):
        return self.name


class ScanResult(models.Model):
    for_scan = models.ForeignKey(Scan)
    output = models.CharField(max_length=255, blank=True, null=True)
    started_on = models.DateTimeField()
    finished_on = models.DateTimeField(blank=True, null=True)
    finished_ok = models.BooleanField()

    class Meta:
        ordering = ('-id', )


class Blacklist(models.Model):
    """Store excluded addresses and a description of the request.

    Each request (coming from an individual or an organization) creates a new
    blacklist entry. As such, if one request contains multiple hosts, they are
    recorded together in the entry, alongside the description of the request.

    targets -- targets to exclude, in CIDR, range, or hostname form
    desc -- (detailed) description of the request
    """
    targets = models.TextField()
    desc = models.TextField()

    def __unicode__(self):
        return self.desc
