# There should be multiple nodes, one per functional application unit; for now
# we ignore this and stick everything in one VM, via common.pp

include node::common

# Default to root:root 0644 ownership
File {
    owner => root,
    group => root,
    mode => '0644',
}
