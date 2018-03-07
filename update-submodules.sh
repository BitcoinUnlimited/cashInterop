#!/bin/bash 
# helper to update the submodules to the latest specified branches

if [ "$1" == "-h" ]; then
  echo "Usage: ./`basename $0` [bu_branch_name] [abc_branch_name] [xt_branch_name]"
  echo " omit the arguments to get defaults: " 
  echo " - BU to use dev branch" 
  echo " - ABC and XT to use master branch" 
  echo " "
  echo "Examples: "
  echo "   ./`basename $0` dev master master"
  echo "or    "
  echo "   ./`basename $0` "
  exit 0
fi

BU_BRANCH=$1
shift
if [ -z $BU_BRANCH ]; then
  echo "Use default dev branch for BU";
  BU_BRANCH=${1:-dev}  
fi

ABC_BRANCH=$1
shift
if [ -z $ABC_BRANCH ]; then
  echo "Use default master branch for ABC";
  ABC_BRANCH=${2:-master}  
fi

XT_BRANCH=$1
shift
if [ -z $XT_BRANCH ]; then
  echo "Use default master branch for XT";
  XT_BRANCH=${3:-master}  
fi

echo " "
echo "----------------------------------------------------- "
echo "Check out BU: ${BU_BRANCH}"
cd bucash 
pwd
git checkout $BU_BRANCH && git pull --ff origin $BU_BRANCH 
echo "BU is updated!"
echo " "

echo "Check out ABC: ${ABC_BRANCH}"
cd ../abc
pwd
git checkout $ABC_BRANCH && git pull --ff origin $ABC_BRANCH 
echo "ABC is updated!"
echo " "

echo "Check out XT: ${XT_BRANCH}"
cd ../xt
pwd
git checkout $XT_BRANCH && git pull --ff origin $XT_BRANCH 
echo "XT is updated!"
echo " "
echo "----------------------------------------------------- "
