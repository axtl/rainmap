# configure python-related components, such as pip

class setup::python {

    package {
        'python-pip':
            ensure => installed,
            require => Yumrepo['epel-6'];
    }

}
