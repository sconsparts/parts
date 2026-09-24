cmake_minimum_required(VERSION 3.10)
project(ninja_main C)
add_executable(ninja_main ninja_main.c)
install(TARGETS ninja_main DESTINATION bin)
