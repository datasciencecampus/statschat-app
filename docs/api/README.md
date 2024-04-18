<h1>Explore the API</h1>

<p>The ONS StatsChat API lets you retrieve ONS publications based on search question.</p>

<h2>Principle Endpoints</h2>

<table class="table">
    <thead class="table--head">
    <th scope="col" class="table--header--cell">Method</th>
    <th scope="col" class="table--header--cell">Endpoint</th>
    <th scope="col" class="table--header--cell">Description</th>
    </thead>
    <tbody>
    <tr class="table--row">
        <td class="table--cell">GET</td>
        <td class="table--cell"><a href="search.md">/search</a></td>
        <td class="table--cell">
            Search for a question.
        </td>
    </tr>
    <tr class="table--row">
        <td class="table--cell">POST</td>
        <td class="table--cell">/feedback</td>
        <td class="table--cell">
            Post feedback on search results.
        </td>
    </tr>
    <tr class="table--row">
            <td class="table--cell">GET</td>
            <td class="table--cell">/datasets</td>
            <td class="table--cell">
                TODO: Search datasets.
            </td>
        </tr>
    <tr class="table--row">
        <td class="table--cell">POST</td>
        <td class="table--cell">/bulk</td>
        <td class="table--cell">
            TODO: Runs a batch of search terms.
        </td>
    </tr>
   </tbody>
</table>

<h2>Custom Endpoints</h2>

<table class="table">
    <thead class="table--head">
    <th scope="col" class="table--header--cell">Method</th>
    <th scope="col" class="table--header--cell">Endpoint</th>
    <th scope="col" class="table--header--cell">Description</th>
    </thead>
    <tbody>
    <tr class="table--row">
        <td class="table--cell">GET</td>
        <td class="table--cell"><a href="?.md"></a></td>
        <td class="table--cell">
            No custom endpoint implemented
        </td>
    </tr>

  </tbody>
</table>


<h2>Supplementary Endpoints</h2>

<table class="table">
    <thead class="table--head">
    <th scope="col" class="table--header--cell">Method</th>
    <th scope="col" class="table--header--cell">Endpoint</th>
    <th scope="col" class="table--header--cell">Description</th>
    </thead>
    <tbody>
    <tr class="table--row">
        <td class="table--cell">GET</td>
        <td class="table--cell">/</td>
        <td class="table--cell">
            Get version information.
        </td>
    </tr>
    <tr class="table--row">
        <td class="table--cell">GET</td>
        <td class="table--cell">/options</td>
        <td class="table--cell">
            TODO: Return something useful
        </td>
    </tr>
    </tbody>
</table>
