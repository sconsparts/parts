#pragma once

/* An unused static function. Under -Wall this triggers -Wunused-function when
 * the header is compiled into a translation unit that does not use it. Brought
 * in via -I (a normal dependency) with the consumer building -Werror, that
 * warning fails the build; brought in via -isystem (a system dependency) the
 * compiler suppresses it and the build succeeds. The gold test relies on that
 * difference. */
static int provider_unused(void)
{
    return 0;
}
