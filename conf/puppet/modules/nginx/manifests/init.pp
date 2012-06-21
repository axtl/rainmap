class nginx {

    package {
        'nginx':
            ensure => installed;
    }

    file {
        'nginx.conf':
            path => '/srv/rainmap/conf/nginx/nginx.conf',
            ensure => present,
            source => 'puppet:///modules/nginx/nginx.conf',
            notify => Service['nginx'];
    }

    service {
        'nginx':
            enable => true,
            ensure => running,
            require => Package['nginx'];
    }
}
