## What is Parts
Parts is an extension to SCons. It augments SCons by adding new concepts to aid with the development, organization, and maintenance of large projects. Parts provides a standardized way to create plug-and-play components within or between products, saving time and development costs.

Parts was originally developed at Intel in an effort to simplify our own usage of SCons when building large software projects. Open sourcing Parts is in an effort to improve SCons and to continue to develop Parts for the benefit of the larger software development community.

## Our Philosophy
Any developer can build the product: A product should always be buildable by any developer, not just on a special box or by special people with special knowledge.
Extend SCons, do not wrapper it: Instead of making a tool that hides the use of SCons, we use the ability of SCons to extend logic and functionality naturally. This means we use SCons as is, but get some extras for free. It also means the ideal build functionality of SCons should work as documented and our new logic should work on top of this.
Help make SCons better: Strive to help show new ideas that can be moved into SCons to improve the extensibility and usefulness of SCons as a build platform.

## Install

pip install scons-parts

## Requirements

- Python 3.11 or later
- SCons 4.0+

## Documentation

Full documentation is available at [https://sconsparts.github.io/](https://sconsparts.github.io/)

## License

This project is licensed under the terms of the [MIT](LICENSE-MIT) open source license. Please refer to [LICENSE](LICENSE) for the full terms.
