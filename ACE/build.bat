set ACE_ROOT=%CD%
set SSL_ROOT=C:\OpenSSL
perl %ACE_ROOT%\bin\mwc.pl -type vc10 -static -features ssl=1 -features uses_wchar=1 -features ipv6=1 -expand_vars ace protocols
