export PBASE=`pwd`

export PATH=$PBASE/bin
export PYTHONPATH=$PBASE/lib/python.zip:$PBASE/lib/python:$PBASE/lib/jumpscale:$PBASE/lib/pythonbin:$PBASE/lib/pythonbin/lib-dynload:$PBASE/bin
export PYTHONHOME=$PBASE

export LIBRARY_PATH="$PBASE/bin:$PBASE/lib"
export LD_LIBRARY_PATH="$LIBRARY_PATH"

export LDFLAGS="-L$LIBRARY_PATH/"

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

export PS1="JS9: "        

