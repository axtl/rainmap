# we're currently only supporting CentOS, sanity check that here

class setup {
    case $operatingsystem {
        CentOS: {
            include setup::repos
        }

        default: {
            fail("Unsupported OS, please submit patches to make it work!")
        }
    }
}
