<h1>/search</h1>

<p>Search for an answer to free text question.</p>

<h2>Request</h2>

<p><code>GET /search</code></p>


<h3>Query parameters</h3>

<table class="table">
        <thead class="table--head">
        <th scope="col" class="table--header--cell">Parameter name</th>
        <th scope="col" class="table--header--cell">Value</th>
        <th scope="col" class="table--header--cell">Description</th>
        <th scope="col" class="table--header--cell">Additional</th>
        </thead>
    <tbody>
        <tr class="table--row">
            <td class="table--cell">q</td>
            <td class="table--cell">string</td>
            <td class="table--cell">Free text question.</td>
            <td class="table--cell">
                Required
             </td>
        </tr>
        <tr class="table--row">
            <td class="table--cell">latest</td>
            <td class="table--cell">string</td>
            <td class="table--cell">TODO: Weight to prioritise latest publication. (0 = No prioritisation)</td>
            <td class="table--cell">
                Optional
                <br>Default: NA
            </td>
        </tr>
         <tr class="table--row">
            <td class="table--cell">limit</td>
            <td class="table--cell">string</td>
            <td class="table--cell">TODO: Specifies the number of references to return.</td>
            <td class="table--cell">
                Optional
                <br>Default: 10
                <br>Maximum: 100
            </td>
        </tr>
     </tbody>
  </table>


<h2>Responses</h2>

<h3>200</h3>
<p>Success. A json return of answer and references.</p>

<h3>400</h3>
<p>Bad request. Indicates an issue with the request. Further details are provided in the response.</p>

<h3>429</h3>
<p>TODO: Server too busy. The Address Index API is experiencing exceptional load.</p>

<h3>500</h3>
<p>TODO: Internal server error. Failed to process the request due to an internal error.</p>




   <h2>CURL example</h2>

   <pre><code>curl #API_URL#/search?q=how+many+people+watched+coronation</code></pre>


   <h2 class="saturn">Sample Output (Concise)</h2>

   <pre><code>
{
    "answer":"Around 6 in 10 people reported they watched, or planned to watch, the Coronation Service on TV.",
    "confidence":"55%",
    "references":[
        {
            "context":"... reported by adults who said their cost of living had increased compared with a month ago were an increase in the price of food shopping (96%), an increase in gas or electricity bills (74%), and an increase in the price of fuel (38%). Around 6 in 10 (59%) reported watching (or planning to watch) the coronation of King Charles III and Camilla, Her Majesty the Queen on TV; this proportion increased with age, being reported by 39% of people aged 16 to 29 years, 56% of those aged 30 to 49 ...",
            "date":"19 May 2023",
            "figures":[],
            "score":"55%",
            "section":"1. Main Points",
            "section_url":"https://www.ons.gov.uk/peoplepopulationandcommunity/wellbeing/bulletins/publicopinionsandsocialtrendsgreatbritain/4to14may2023#main-points",
            "source":"2023-05-19_public-opinions-and-social-trends-great-britain-4-to-14-may-2023",
            "title":"Public opinions and social trends, Great Britain: 4 to 14 May 2023",
            "url":"https://www.ons.gov.uk/peoplepopulationandcommunity/wellbeing/bulletins/publicopinionsandsocialtrendsgreatbritain/4to14may2023"
        },
        {
            "context":"... Her Majesty the Queen, took place on 6 May 2023, during the latest period of our survey.We asked adults what activities they did or planned to do over the coronation weekend, 6 to 8 May 2023. Around 6 in 10 (59%) people reported they watched, or planned to watch, the Coronation Service on TV. This proportion increased with age, being reported by:  39% of those aged 16 to 29 years 56% of those aged 30 to 49 years 62% of those aged 50 to 69 years 82% of those aged 70 years or over  Figure ...",
            "date":"19 May 2023",
            "figures":[
                {
                    "figure_subtitle":"Proportion of all adults in Great Britain, 4 to 14 May 2023",
                    "figure_title":"Figure 5: Around 6 in 10 (59%) adults reported they planned to or did watch the Coronation Service on TV","figure_type":"chartbuilder_image",
                    "figure_url":"https://www.ons.gov.uk/chartimage?uri=/peoplepopulationandcommunity/wellbeing/bulletins/publicopinionsandsocialtrendsgreatbritain/4to14may2023/59504068&width=&hideSource=true"
                }
            ],
            "score":"55%",
            "section":"6. King\u2019s coronation",
            "section_url":"https://www.ons.gov.uk/peoplepopulationandcommunity/wellbeing/bulletins/publicopinionsandsocialtrendsgreatbritain/4to14may2023#kings-coronation",
            "source":"2023-05-19_public-opinions-and-social-trends-great-britain-4-to-14-may-2023",
            "title":"Public opinions and social trends, Great Britain: 4 to 14 May 2023",
            "url":"https://www.ons.gov.uk/peoplepopulationandcommunity/wellbeing/bulletins/publicopinionsandsocialtrendsgreatbritain/4to14may2023"
        }
    ]
}
   </code></pre>
