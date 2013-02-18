# setup extra yum repositories
# ref: http://rene.bz/yum-repo-and-package-dependencies-puppet/

class setup::repos {
    # setup EPEL, RabbitMQ, PostgreSQL

    # keyfile for repository
    file {
        'RPM-GPG-KEY-EPEL-6':
            path => '/etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6',
            mode => 0444,
            source => 'puppet:///modules/setup/RPM-GPG-KEY-EPEL-6-0608B895';
            # source => 'https://fedoraproject.org/static/0608B895.txt';
        'RPM-GPG-KEY-PGDG-91':
            path => '/etc/pki/rpm-gpg/RPM-GPG-KEY-PGDG-91',
            mode => 0444,
            source => 'puppet:///modules/setup/RPM-GPG-KEY-PGDG-91';
    }

    yumrepo {
        'epel-6':
            baseurl => 'http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm',
            mirrorlist => 'http://mirrors.fedoraproject.org/mirrorlist?repo=epel-6&arch=$basearch',
            enabled => 1,
            gpgcheck => 1,
            gpgkey => 'file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-6',
            require => File['RPM-GPG-KEY-EPEL-6'];

        'pgdg-91-redhat':
            baseurl => 'http://yum.postgresql.org/9.1/redhat/rhel-$releasever-$basearch',
            enabled => 1,
            gpgcheck => 1,
            gpgkey => 'file:///etc/pki/rpm-gpg/RPM-GPG-KEY-PGDG-91',
            require => File['RPM-GPG-KEY-PGDG-91'];
    }
}
