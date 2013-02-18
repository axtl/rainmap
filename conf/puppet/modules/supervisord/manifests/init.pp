class supervisord {

    package {
        'supervisord':
            provider => pip,
            ensure => '3.0a12';
    }

    file {
        'supervisord.conf':
            path => '/srv/rainmap/conf/supervisord/supervisord.conf',
            ensure => present,
            source => 'puppet:///modules/supervisord/supervisord.conf',
            notify => Service['supervisord'];

        '*.ini':
            path => '/srv/rainmap/conf/supervisord/',
            ensure => present,
            source => 'puppet:///modules/supervisord/*.ini',
            notify => Service['supervisord'];
    }

    service {
        'supervisord':
            enable => true,
            ensure => running,
            require => Package['supervisord'];
    }
}
