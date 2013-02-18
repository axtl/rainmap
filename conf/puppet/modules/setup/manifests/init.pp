# we're currently only supporting CentOS, sanity check that here

class setup {
    case $operatingsystem {
        CentOS: {
            notify("OS check passed")
        }

        default: {
            fail("Unsupported OS, please submit patches to make it work!")
        }
    }
}
