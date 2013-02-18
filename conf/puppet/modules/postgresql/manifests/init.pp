class postgresql {

    $packages = {
        'postgresql91-libs' => {},
        'postgresql91' => {},
        'postgresql91-server' => {},
    }

    $package_defaults = {
        ensure => latest,
        require => Yumrepo['pgdg-91-redhat'],
    }

    create_resources(package, $packages, $package_defaults)

    service {
        'pgsql':
            enable => true,
            ensure => running,
            require => Package['postgresql91-libs', 'postgresql91',
                                'postgresql91-server'];
    }
}
