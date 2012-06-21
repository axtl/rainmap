# There should be multiple nodes, one per functional application unit; for now
# we ignore this and stick everything in one VM, via common.pp

import "common.pp"

# Default to root:root 0644 ownership
File {
    owner => 0,
    group => 0,
    mode => "0644",
}
