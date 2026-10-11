$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue
$inputFile = "C:\IIITH\Hackathon\megathon26-tablespoon\deliverables\GreenLens_AI_Final_Deck.pptx"
$outputFile = "C:\IIITH\Hackathon\megathon26-tablespoon\deliverables\GreenLens_AI_Final_Deck.pdf"
$pres = $ppt.Presentations.Open($inputFile, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
$pres.SaveAs($outputFile, 32)
$pres.Close()
$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
Write-Host "PDF exported successfully to $outputFile"
