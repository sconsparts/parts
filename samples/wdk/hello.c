#include <ntddk.h>

__declspec(dllimport) int library_function(int argument);

NTSTATUS DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath)
{
    DbgPrint("Hello, World\n");

    library_function(1);

    return STATUS_SUCCESS;
}

/* vim: set et ts=4 sw=4 ai */

