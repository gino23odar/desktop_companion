# Run from any directory. Set -OpenScad to the full path if not on PATH.
param([string]$OpenScad = 'openscad.com')
$ErrorActionPreference = 'Stop'
$parts = @('front_shell','rear_shell','esp_cradle','tail','screen_fit','magnet_fit','usb_fit','rail_fit')
foreach ($part in $parts) {
    $folder = if ($part -in @('front_shell','rear_shell','esp_cradle','tail')) {'stl'} else {'prototypes'}
    $destination = Join-Path $PSScriptRoot "..\$folder"
    New-Item -ItemType Directory -Force -Path $destination | Out-Null
    $output = Join-Path $destination "$part.stl"
    # OpenSCAD's -D argument must include literal quotes around the string.
    # PowerShell 7 passes the quoted value; legacy Windows PowerShell needs escaping.
    $definition = if ($PSVersionTable.PSVersion.Major -lt 7) { 'part=\"' + $part + '\"' } else { 'part="' + $part + '"' }
    & $OpenScad --export-format binstl -o $output -D $definition (Join-Path $PSScriptRoot 'svinka.scad')
    if ($LASTEXITCODE -ne 0) { throw "OpenSCAD export failed for $part" }
}
