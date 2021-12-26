/* IMPORT */
const notion_api = require("@notionhq/client")

const NOTION_API_KEY = 'secret_ly0rxwsJPkokeDOXYZoGR5GAcKEZPC6ZVlYYnO1JfoU'
const NOTION_DATABASE_ID = '1755f2a9e4b84d42bba313a65a40de37'

const notion = new notion_api.Client({ auth: NOTION_API_KEY })

const databaseId = NOTION_DATABASE_ID

async function addItem(text) {
  try {
    const response = await notion.pages.create({
      parent: { database_id: databaseId },
      properties: {
        title: {
          title:[
            {
              "text": {
                "content": text
              }
            }
          ]
        }
      },
    })
    console.log(response)
    console.log("Success! Entry added.")
  } catch (error) {
    console.error(error.body)
  }
}

addItem('from JS')
