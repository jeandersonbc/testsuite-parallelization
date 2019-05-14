#!/bin/bash
#
# This script is related to the RQ5. It compares test execution with
# default settings (assuming some parallel configuration) and
# sequential execution.
#
# This script depends on the "dynamic-variables.csv" file to know
# which projects have parallelism enabled by default (generated by the
# parsettings.sh script).
#
# Author: Jeanderson Candido <http://jeandersonbc.github.io>
#
SCRIPTS=./src
PROJECTS_DIR=./src/downloads
INPUT_CSV=./src/dynamic-variables.csv

if [ ! -f "$INPUT_CSV" ]; then
    echo "This script depends on the \"dynamic-variables.csv\" file to know which projects "
    echo "have parallelism enabled by default (generated by the echo \"parsettings.sh\" script)."
    echo "MISSING FILE!"
    exit 1
fi

MAVEN_SKIPS="-Drat.skip=true -Dmaven.javadoc.skip=true \
             -Djacoco.skip=true -Dcheckstyle.skip=true \
             -Dfindbugs.skip=true -Dcobertura.skip=true \
             -Dpmd.skip=true -Dcpd.skip=true"

BASEDIR="`pwd`"
for subject in `cat $INPUT_CSV | sed "s/,.*//g" | uniq`; do
    project_path=$PROJECTS_DIR/$subject
    [[ ! -d "$project_path" ]] && continue

    # "sequentialize" pom files
    $SCRIPTS/sequentializer.rb -p "$project_path"

    cd $project_path

    mvn clean dependency:go-offline 2>&1
    mvn compile test-compile -DskipTests $MAVEN_SKIPS 2>&1
    timeout -s SIGKILL 90m mvn test -fae $MAVEN_SKIP 2>&1 | tee sequential.log

    # undo changes on this subject
    git reset --hard HEAD

    cd $BASEDIR
done
