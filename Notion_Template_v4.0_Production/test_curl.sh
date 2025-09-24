#!/bin/bash
source .env
curl -X GET "https://api.notion.com/v1/pages/277a6c4ebadd80799d19d839db90e901" \
  -H "Authorization: Bearer $NOTION_TOKEN" \
  -H "Notion-Version: 2022-06-28"
