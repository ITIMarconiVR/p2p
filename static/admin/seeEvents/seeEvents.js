document.addEventListener("DOMContentLoaded", () => {
    let currentDate = new Date();

    const lessonsTable1 = document
        .getElementById("lessons-table-1")
        .querySelector("tbody");
    const lessonsTable2 = document
        .getElementById("lessons-table-2")
        .querySelector("tbody");
    const title = document.getElementById("titolo");
    const prevDayButton = document.getElementById("prev-day");
    const nextDayButton = document.getElementById("next-day");

    function updateDateDisplay() {
        const formattedDate = currentDate.toLocaleDateString();
        today = new Date();
        if (currentDate.toDateString() === today.toDateString()) {
            title.textContent = `Lezioni di oggi`;
            document.title = `Admin - Lezioni di oggi`;
            return;
        }
        title.textContent = `Lezioni del ${formattedDate}`;
        document.title = `Admin - Lezioni del ${formattedDate}`;
    }

    function fetchLessons(date) {
        fetch("/lezioni2?matricolaT=%&data=" + formatDate(date))
            .then((response) => response.json())
            .then((data) => {
                lessonsTable1.innerHTML = "";
                lessonsTable2.innerHTML = "";
                if (Array.isArray(data)) {
                    data.forEach((lesson, index) => {
                        const row = (
                            lesson.ora === 1 ? lessonsTable1 : lessonsTable2
                        ).insertRow();
                        const cellIndex = row.insertCell(0);
                        const cellData = row.insertCell(1);
                        const cellOra = row.insertCell(2);
                        const cellTutor = row.insertCell(3);
                        const cellTutee = row.insertCell(4);

                        cellIndex.textContent = index + 1;
                        cellOra.textContent =
                            lesson.ora === 1 ? "13.40" : "14.30";
                        datadate = new Date(lesson.data);
                        dataFormatted = datadate.toISOString().split("T")[0];
                        dataFormatted = dataFormatted
                            .split("-")
                            .reverse()
                            .join("/");
                        cellData.textContent = dataFormatted;
                        cellTutor.textContent = `${lesson.nomeP} ${lesson.cognomeP} ${lesson.classeP}`;
                        cellTutee.textContent = `${lesson.nomeT} ${lesson.cognomeT} ${lesson.classeT}`;
                    });
                } else {
                    const row1 = lessonsTable1.insertRow();
                    const cell1 = row1.insertCell(0);
                    cell1.colSpan = 5;
                    cell1.textContent = "Nessuna lezione per oggi alle 13.40.";

                    const row2 = lessonsTable2.insertRow();
                    const cell2 = row2.insertCell(0);
                    cell2.colSpan = 5;
                    cell2.textContent = "Nessuna lezione per oggi alle 14.30.";
                }
            })
            .catch((error) => {
                console.error(
                    "Errore durante il recupero delle lezioni:",
                    error
                );
            });
    }

    prevDayButton.addEventListener("click", () => {
        currentDate.setDate(currentDate.getDate() - 1);
        updateDateDisplay();
        fetchLessons(currentDate);
    });

    nextDayButton.addEventListener("click", () => {
        currentDate.setDate(currentDate.getDate() + 1);
        updateDateDisplay();
        fetchLessons(currentDate);
    });

    // Initial fetch and display
    updateDateDisplay();
    fetchLessons(currentDate);

    function formatDate(date) {
        return date.toISOString().split("T")[0];
    }


    function generaPDF(date) {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF("p", "mm", "a4");

        const strdata = formatDate(date);

        doc.setFont("helvetica", "bold");
        doc.setFontSize(16);
        // doc.text("Peer2Peer: " + strdata, 14, 10);

        fetch("/lezioni2?matricolaT=%&data=" + strdata)
            .then((response) => response.json())
            .then((data) => {
                if (Array.isArray(data)) {
                    data = data.sort((a, b) => a.ora - b.ora);
                    const lessons = data.map((lesson) => {
                        const {data, ora, nomeP, cognomeP, classeP, nomeT, cognomeT, classeT, } = lesson;
                        return [
                            new Date(data).toISOString().split("T")[0],
                            ora === 1 ? "13:40" : "14:30",
                            `${nomeP} ${cognomeP}\n(${classeP})`,
                            `${nomeT} ${cognomeT}\n(${classeT})`,
                            " ",
                            " ",
                        ];
                    });

                    doc.autoTable({
                        head: [["Data", "Ora", "Tutor", "Tutorato", "Aula",  "Firma"]],
                        body: lessons,
                        theme: "grid",
                        styles: { fontSize: 10, cellPadding: 2 },
                        headStyles: {
                            fillColor: [255, 255, 255],
                            textColor: 0,
                            fontSize: 11,
                        },
                        columnStyles: {
                            0: { cellWidth: 25 },
                            1: { cellWidth: 15 },
                            2: { cellWidth: 45 },
                            3: { cellWidth: 45 },
                            4: { cellWidth: 15 },
                            5: { cellWidth: 45 },
                        },
                    });

                    const name = `Peer2Peer_${strdata}.pdf`;
                    doc.save(name);
                }
            })
            .catch((error) =>
                console.error("Errore nel recupero dati:", error)
            );
    }

    document.getElementById("pdf-button").addEventListener("click", () => {
        generaPDF(currentDate);
    });
});
