PROD_APP_ID:=fc618bee-352f-461a-95b5-bc0a2395302a
PROD_APP_NAME:=Template DO NOT USE
TEST_APP_ID:=5e842053-7364-4a90-a275-2bd838458fef

# Generate a WARNING for PROD_APP_NAME if set to 'Template DO NOT USE'
ifeq (${PROD_APP_NAME}, 'Template DO NOT USE')
  $(warning '**** PROD_APP_NAME is set to Template DO NOT USE ****') 
endif
