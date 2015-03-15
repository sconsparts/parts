module hello_mod
contains
    subroutine print_hello(world)
        character*(*), intent(in) :: world
        print *, 'Hello', world
    end subroutine print_hello
end module hello_mod
