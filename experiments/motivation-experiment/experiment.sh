#!/bin/bash
BASE_DIR="`pwd`"

# Input parameters
PROJECT_PATH=$1
TEST_PATH=$2

# Assuming the relative path to test directory as "PROJECT_PATH"
[[ -z "$TEST_PATH" ]] && TEST_PATH="."

if [[ -z "$PROJECT_PATH" ]]; then
    echo "Usage: ./experiment.sh <PROJECT_PATH> [<TEST_PATH>]"
    exit 1
fi

../scripts/generate_versions.sh "$PROJECT_PATH" "$TEST_PATH"

NAME="`basename "$PROJECT_PATH"`"
LOGNAME_PREFIX="`date +"$NAME-%m%d%H%M%S"`"
SAMPLE_HOME="$BASE_DIR/samples/$NAME"

MVN_BUILD_CMD="mvn -Dmaven.javadoc.skip=true -DskipTests clean install"
MVN_TEST_CMD="mvn -Dmaven.javadoc.skip=true test"

# SETUP
echo "Compiling base version"
if [ ! -d "$SAMPLE_HOME/seq" ]; then
    echo "Base version missing!"
    exit 1
fi

cd "$SAMPLE_HOME/seq"
if [ -f 'pom.xml' ]; then
    $MVN_BUILD_CMD &>/dev/null
else
    echo "Unsupported build system!"
    exit 1
fi
cd "$BASE_DIR"

# BEGINNING ELAPSED TIME EXPERIMENT
echo -e "Measuring elapsed time for different running settings\n"
for version in `ls $SAMPLE_HOME`; do
    LOG_FILE="$BASE_DIR/$LOGNAME_PREFIX-$version-timelog.txt"

    echo -e "\n\t* Running setup \"$version\""
    cd "$SAMPLE_HOME/$version/$TEST_PATH"
    if [ -f 'pom.xml' ]; then
        TEST_COMMAND=$MVN_TEST_CMD
    else
        echo "Unsupported build system!"
        exit 1
    fi
    /usr/bin/time -v $TEST_COMMAND &> $LOG_FILE
    cat $LOG_FILE | grep "Elapsed (wall clock) time"
    cd "$BASE_DIR"
done
# END OF ELAPSED TIME EXPERIMENT

echo -e "\nRunning Flakiness analysis"
for version in `ls $SAMPLE_HOME`; do
    dir_path="$SAMPLE_HOME/$version/$TEST_PATH"
    echo -e "\n* Running setup \"$version\""
    if [ -d "$dir_path" ]; then
        ./flakiness_experiment.py "$dir_path" "$LOGNAME_PREFIX-$version"
    fi
done
