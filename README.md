# Teacher's Pet
#### Description: A website that helps teachers organize and manage their classes.

**Teacher's Pet** is a classroom management system I built to make teachers’ lives a little easier. The idea behind the project is simple: instead of juggling papers, spreadsheets, and sticky notes, teachers can have everything about their classes organized in one place. From adding students to tracking exam results and planning lessons, this system helps keep everything neat and accessible.  

With Teacher's Pet, teachers can create multiple classes and manage them all from a single account. Each class can have students added or removed easily. Teachers can also create exams for each class and record scores. The results are displayed clearly, making it easy to see how students are performing at a glance. If needed, scores can be updated or deleted with just a few clicks.  

The project also allows teachers to add lesson plans and class notes. Lesson plans can be attached to specific dates, helping teachers organize their teaching schedule. Class notes are perfect for reminders or important information about a class. Every teacher sees only their own classes and students, which keeps everything private and secure.  

## How it works

The system is built with **Python and Flask**, which handle the backend logic, and **HTML, CSS, and a little JavaScript** for the interface. All data is stored in a **SQLite database**, which keeps track of teachers, students, classes, exams, and notes.  

When a teacher logs in, they can see a list of their classes, along with counts of students, exams, and notes for each class. Clicking on a class brings up more details, like the students in that class, their exam scores, and lesson plans. Forms and buttons make it easy to add or remove students, create exams, and enter scores. Popups are used for entering scores so the page doesn’t have to reload every time, making it quicker and more convenient.  

The interface is designed to be simple and easy to navigate. Tables are used to display data clearly, and buttons are placed where actions need to be taken, such as removing a student or deleting a score. Tooltips and icons give extra information when needed without cluttering the page.  

## Design choices

While building this project, I made several decisions to make the system practical and easy to use. For example, the database is simple but organized so that all data is connected correctly, like students belonging to a class and exams linked to that class. The user interface focuses on clarity rather than flashy design, so teachers can quickly find the information they need.  

Security was also a priority. Each teacher has access only to their own classes and data. This means sensitive student information stays private, and teachers can confidently manage their classes online.  

## Possible improvements

If I continue working on Teacher's Pet, I could add features like exporting student results as PDF or Excel files, sending notifications to students, or creating a dashboard to give teachers a quick overview of class performance. Another idea would be to add student logins so they can view only their own scores and notes.  

Overall, Teacher's Pet is a practical tool for managing classrooms. It keeps everything organized, makes tracking student progress easier, and saves teachers time. I’m proud of how it combines functionality with a simple, user-friendly interface, and it’s ready to be used as a teaching assistant in the digital classroom.
