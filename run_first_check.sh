# Exit on non-zero exit code
set -e
KEYS=(
    MODULE
    PROD_APP_ID
    APP_NAME
    TEST_APP_NAME
    TODO
)
VALUES=(
    illinois_app
    fc618bee-352f-461a-95b5-bc0a2395302a
    "Illinois Test Template app"
    "Test Box"
    TODO
)

for i in ${!VALUES[@]}; do 
    if git grep "${VALUES[$i]}" -- :^run_first_check.sh
    then
        echo "Failed to update ${KEYS[$i]}!" && exit 1
    fi
done

if [ -f ".github/workflows/run_first_check.yml" ]; then
    echo Remove run_first_check.yml
fi
echo Remove run_first_check.sh
exit 1
