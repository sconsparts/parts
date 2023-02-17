***************
Release  0.17.2
***************

* Fix bug in how components with `optional=True` are handled that cause crash.
* Fix a edge cases with how rpm spec files would be generted with the `Requires:` tag that inserted extra commas in the line. This could cause build failures with rpm_build
* Fix a case in which part_dir and src_dir would not be correct resulting in a failed build.
* Add a number of tests cases
