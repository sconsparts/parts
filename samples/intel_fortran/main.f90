program hello
use hello_mod
implicit none
character*(*), parameter :: world = "world!"
call print_hello(world)
end program hello
