class node::common inherits node::base {
    # all the bits go into one big bucket---this one
    include supervisord
    include nginx
    include rabbitmq
    include postgresql
}
