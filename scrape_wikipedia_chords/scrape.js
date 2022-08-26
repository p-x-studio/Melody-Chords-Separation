let out = {}

function removeMultipleWhite(text) {
    return text.replace(/\s+/g, ' ').trim()
}

$('table.wikitable:nth-child(6) tr').each(function(){
    let chordKind = undefined

    $(this).find('td').each((i, td) => {
        const textContent = removeMultipleWhite(td.textContent.replace(" chord", ""))

        if (i === 0) {
            chordKind = textContent.replace("[1]", "").toLowerCase()
            chordKind = removeMultipleWhite(chordKind)
            chordKind = chordKind.replaceAll(" ", "-")
        } else if (i === 4) {
            let steps = textContent.replaceAll("t", 10).replaceAll("e", 11) 
            steps = steps.split(" ").map(Number)
            
            out[chordKind] = steps
        }
    })
})


console.log(JSON.stringify(out))