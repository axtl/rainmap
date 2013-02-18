# setup application locations

class setup::files {

    $srv = '/srv/rainmap/'

    $files = {
        # create application directories
        '/$srv' => {},
        '/$srv/conf/' => {},
        '/$srv/conf/nginx/' => {},
        '/$srv/conf/supervisord/' => {},
        '/$srv/log/' => {},
        '/$srv/run/' => {},
        '/$srv/storage/' => {},
    }

    $defaults = {
        ensure => directory,
    }

    create_resources(file, $files, $defaults)
}
