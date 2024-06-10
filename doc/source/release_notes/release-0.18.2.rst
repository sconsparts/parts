***************
Release  0.18.2
***************
* Add `add_preload_logic_queue(func)` to allow adding preload logic after all the extensions have been loaded.


Notes
=====

This new function allows you to add preload logic after all the extensions have been loaded. This prevents issue with extensions that rely on the logic defined in other extensions to be called at startup before and Part files are loaded.
