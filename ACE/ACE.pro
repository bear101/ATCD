CONFIG += c++11 c++14

QT -= core gui

HEADERS += $$system("find $${PWD}/ace -name '*.h' -or -name '*.inl'")
HEADERS += $$system("find $${PWD}/protocols/ace/INet -name '*.h' -or -name '*.inl'")

SOURCES += $$system("find $${PWD}/ace -name '*.cpp'")
SOURCES += $$system("find $${PWD}/protocols/ace/INet -name '*.cpp'")

INCLUDEPATH += $${PWD}/ace
INCLUDEPATH += $${HEST}/protocols/ace/INet

TARGET=ACE
