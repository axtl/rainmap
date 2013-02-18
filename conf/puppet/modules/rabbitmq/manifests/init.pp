class rabbitmq {

    $link = 'http://www.rabbitmq.com/releases/rabbitmq-server/v2.8.4/rabbitmq-server-2.8.4-1.noarch.rpm'
    $serialfile = '/var/log/puppet/rabbitmq-server-rpm.serial'
    exec {
        'rabbitmq-server-rpm':
            # fetch, import key, install, mark new version based on upstream
            command => "curl -s -o /tmp/rabbitmq-server.rpm $link \
                        && rpm --import /tmp/rabbitmq-gpgkey \
                        && yum install /tmp/rabbitmq-server.rpm \
                        && echo \"$link\" > \"$serialfile\"",
            unless  => "test \"`cat $serialfile 2>/dev/null`\" = \"$link\"",
            require => File['/tmp/rabbitmq-gpgkey'],
    }

    package {
        'rabbitmq-server':
            ensure => '2.8.4-1',
            # source => 'http://grabbitmq-server-2.8.4-1.noarch.rpm',
            require => Exec['rabbitmq-server-rpm'];
    }

    file {
        '/tmp/rabbitmq-gpgkey':
            owner => root,
            group => root,
            mode => 0444,
            source => 'puppet:///modules/rabbitmq/rabbitmq-signing-key-public.asc';
    }

    service {
        'rabbitmq-server':
            enable => true,
            ensure => running,
            require => Package['rabbitmq-server'];
    }

}
