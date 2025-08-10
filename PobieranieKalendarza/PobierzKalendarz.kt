import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.nio.file.Files
import java.nio.file.Paths
import kotlin.system.exitProcess

// Klasa danych do przechowywania informacji o pojedynczym wydarzeniu
data class LiturgicalEvent(val name: String, val date: String, val type: String, val color: String)

fun main(args: Array<String>) {
    // 1. Walidacja argumentów wejściowych
    if (args.size != 2) {
        println("Błąd: Nieprawidłowa liczba argumentów.")
        println("Sposób użycia: java -jar skrypt.jar <rok> \"<dokładna_ścieżka_do_folderu_docelowego>\"")
        println("Przykład: java -jar skrypt.jar 2025 \"C:\\Uzytkownicy\\Jan\\Pobrane\"")
        exitProcess(1)
    }

    val year = args[0]
    val outputFolderPath = args[1]

    if (year.toIntOrNull() == null) {
        println("Błąd: Podany rok '$year' nie jest prawidłową liczbą.")
        exitProcess(1)
    }

    val baseUrl = "https://gcatholic.org/calendar/ics/YEAR-pl-PL.ics?v=3"
    val finalUrl = baseUrl.replace("YEAR", year)
    println("Próba pobrania danych dla roku: $year z adresu URL: $finalUrl")

    try {
        val url = URL(finalUrl)
        val connection = url.openConnection() as HttpURLConnection
        connection.requestMethod = "GET"
        connection.connect()

        when (connection.responseCode) {
            HttpURLConnection.HTTP_OK -> {
                val icsContent = connection.inputStream.bufferedReader().readText()
                println("Dane ICS pobrane. Rozpoczynam finalne, zaawansowane parsowanie...")

                val jsonContent = parseIcsToJsonAdvanced(icsContent)

                val outputDirectory = Paths.get(outputFolderPath)
                if (!Files.exists(outputDirectory)) {
                    Files.createDirectories(outputDirectory)
                    println("Utworzono folder docelowy: $outputDirectory")
                }

                val fileName = "$year.json"
                val outputPath = outputDirectory.resolve(fileName)
                Files.write(outputPath, jsonContent.toByteArray(Charsets.UTF_8))

                println("Sukces! Plik JSON został wygenerowany i zapisany w: $outputPath")
            }
            HttpURLConnection.HTTP_NOT_FOUND -> {
                println("Informacja: Dane kalendarza dla roku '$year' nie są jeszcze dostępne (Błąd 404).")
            }
            else -> {
                println("Błąd: Serwer odpowiedział nieoczekiwanym kodem: ${connection.responseCode}")
            }
        }
    } catch (e: IOException) {
        println("Wystąpił błąd sieciowy lub błąd zapisu pliku: ${e.message}")
    } catch (e: Exception) {
        println("Wystąpił nieoczekiwany błąd: ${e.message}")
    }
}

fun parseIcsToJsonAdvanced(icsContent: String): String {
    val events = mutableListOf<LiturgicalEvent>()
    val lines = icsContent.lines()

    var inEventBlock = false
    var currentSummary = ""
    var currentDtstart = ""

    var i = 0
    while (i < lines.size) {
        val line = lines[i]

        if (line == "BEGIN:VEVENT") {
            inEventBlock = true
            currentSummary = ""
            currentDtstart = ""
        } else if (line == "END:VEVENT") {
            inEventBlock = false
            if (currentDtstart.isNotEmpty() && currentSummary.isNotEmpty()) {
                val color = parseColor(currentSummary)
                val type = parseType(currentSummary)
                var name = parseName(currentSummary) // Używamy 'var', aby móc modyfikować nazwę

                if (name == "Najświętszej Maryi Panny") {
                    val day = currentDtstart.substring(6, 8)
                    val month = currentDtstart.substring(4, 6)
                    name = "$name ($day-$month)"
                }

                val formattedDate = formatDate(currentDtstart)

                if (name.isNotBlank()) {
                    events.add(LiturgicalEvent(name, formattedDate, type, color))
                }
            }
        } else if (inEventBlock) {
            when {
                line.startsWith("DTSTART;VALUE=DATE:") -> {
                    currentDtstart = line.substringAfter("DTSTART;VALUE=DATE:")
                }
                line.startsWith("SUMMARY:") -> {
                    var summaryBuilder = StringBuilder(line.substringAfter("SUMMARY:"))
                    while (i + 1 < lines.size && lines[i + 1].startsWith(" ")) {
                        i++
                        summaryBuilder.append(lines[i].trimStart())
                    }
                    currentSummary = summaryBuilder.toString()
                }
            }
        }
        i++
    }

    return buildJson(events)
}

fun buildJson(events: List<LiturgicalEvent>): String {
    val jsonBuilder = StringBuilder("{\n")

    events.forEachIndexed { index, event ->
        val cleanedName = event.name.replace("\\", "").replace("\"", "\\\"")
        val cleanedType = event.type.replace("\\", "")
        val cleanedColor = event.color.replace("\\", "")

        jsonBuilder.append("  \"$cleanedName\": {\n")
        jsonBuilder.append("    \"data\": \"${event.date}\",\n")
        jsonBuilder.append("    \"typ\": \"$cleanedType\",\n")
        jsonBuilder.append("    \"kolor\": \"$cleanedColor\"\n")
        jsonBuilder.append("  }")

        if (index < events.size - 1) {
            jsonBuilder.append(",\n")
        } else {
            jsonBuilder.append("\n")
        }
    }

    jsonBuilder.append("}")
    return jsonBuilder.toString()
}

// === Funkcje pomocnicze ===

fun formatDate(dateStr: String): String {
    if (dateStr.length != 8) return dateStr
    val year = dateStr.substring(0, 4)
    val month = dateStr.substring(4, 6)
    val day = dateStr.substring(6, 8)
    return "$day-$month-$year"
}

fun parseColor(summary: String): String {
    if (summary.isBlank()) return "Nieznany"
    // Przeszukuje cały ciąg, aby znaleźć pierwszą pasującą ikonę
    return when {
        summary.contains("⚪") -> "Biały"
        summary.contains("🔴") -> "Czerwony"
        summary.contains("🟢") -> "Zielony"
        summary.contains("🟣") -> "Fioletowy"
        summary.contains("💗") || summary.contains("🩷") -> "Różowy"
        else -> "Nieznany"
    }
}

fun parseType(summary: String): String {
    val match = "\\[(.*?)\\]".toRegex().find(summary)
    val code = match?.groupValues?.get(1) ?: return ""

    return when (code) {
        "U" -> "Uroczystość"
        "Ś" -> "Święto"
        "W" -> "Wspomnienie obowiązkowe"
        "w" -> "Wspomnienie dowolne"
        "w*" -> "Wspomnienie dowolne"
        else -> ""
    }
}

/**
 * CAŁKOWICIE PRZEBUDOWANA, OSTATECZNA WERSJA FUNKCJI CZYSZCZĄCEJ NAZWĘ.
 */
fun parseName(summary: String): String {
    var result = summary

    // Krok 1: Usuń blok z rangą (np. "[W]") oraz następującą po nim spację.
    // Wyrażenie regularne szuka bloku [...] i opcjonalnej spacji po nim.
    result = result.replace(Regex("\\[.*?\\]\\s*"), "")

    // Krok 2: Usuń wszystkie znane ikony emoji reprezentujące kolor.
    val knownIcons = listOf("⚪", "🔴", "🟢", "🟣", "💗", "🩷")
    knownIcons.forEach { icon ->
        result = result.replace(icon, "")
    }

    // Krok 3: Usuń wszystkie znaki zapytania.
    result = result.replace("?", "")

    // Krok 4: Usuń wszelkie wiodące i końcowe białe znaki,
    // a także zamień ewentualne wielokrotne spacje w środku na pojedynczą.
    return result.trim().replace(Regex("\\s+"), " ")
}