class apache {

    package { 'mod_wsgi':
        ensure => installed;
    }

    package { 'httpd':
        require => Package['mod_wsgi'],
        ensure => installed;
    }

    file {
        'confd':
            path => '/srv/rainmap/conf/httpd/conf.d/',
            ensure => directory,
            checksum => mtime,
            mode => 644,
            require => Package['httpd'],
            notify => Service['httpd'];
        'rainmap.conf':
            path => '/etc/httpd/conf.d/rainmap.conf',
            ensure => present,
            source => 'puppet:///modules/:username.to.idapache/rainmap.conf',
            require => File['confd'],
            notify => Service['httpd'];
    }

    service { 'httpd':
        ensure => running,
        enable => true,
        require => Package['httpd'];
    }
}
