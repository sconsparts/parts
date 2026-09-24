cmake_minimum_required(VERSION 3.10)
project(um_main C)
add_executable(um_main um_main.c)
install(TARGETS um_main DESTINATION bin)
