# Design document for zmovies

## Overview
 
Zmovies is a personal web application that displays information about the movies that I have watched.

It presents a read-only view, no editing, adding, or updating functionality is provided.
It is driven by CSV data, edited and updated offline.

## Data

The application is driven by data stored in CSV files in the "Datadir" directory.

The CSV files are actually exported from the Letterboxd online platform, which is a social network for sharing movie reviews and lists.
The exported CSV files contain information about the movies that I have watched, and the diary of my viewings.
There are no reviews or ratings used anywhere in the data (even though the Letterboxd platform supports them), as I do not use these features.

The data are read in the initial load of the application, maybe transformed in some way for more efficient access.

The data actually contain, for each movie, only the title and the year of release, with an additional link to the actual movie page on Letterboxd. This may be used in the future to acquire more data about the movies, like the director and the cast. Also getting the poster image for each movie may be useful for a more visually appealing presentation.

All this data maybe stored in a local SQLite database for more efficient access, and to allow for future extensions of the application. Then, upon startup, the application will read the CSV files and update the database with any new data.

## Data model

Essentially the data model is a list of movies, each movie having a title, a year of release, and a link to the Letterboxd page.
Then we have the viewings, which are a list of dates when I watched each movie.

If additional data is acquired via the Letterboxd page, the data model may be extended to include the director and the cast of each movie. This will probably be implemented as list of people and relationships between them and the movies.

## Presentation

The application presents the data in a simple and clean way, with a focus on the movies that I have watched.

Different views are provided:
- movies (ordered by title, by year, by director)
- diary (ordered by date of viewing, title, director)
- search for movie by title, director, cast member

As is typical for such applications, the main "view" will be a table/list view of movies (probably as search results), showing the various fields in columns, with the ability to sort by each column.
There might be need for a card/entry/detail view for each movie, showing the information in a more detailed way.

## Technology

The application is built entirely in Python and is designed to run on a Linux host.
No JavaScript build tooling or Node.js is required.

| Concern | Choice | Notes |
|---------|--------|-------|
| Language | **Python** | Primary implementation language |
| Web framework | **Flask** | Lightweight, server-rendered pages |
| Templating | **Jinja2** | Ships with Flask; renders the list, diary, and detail views |
| Client interactivity | **HTMX** | Partial-page updates (sorting, search) without hand-written JavaScript |
| Styling | **Pico.css** | Minimal, classless CSS framework loaded via CDN |
| Database | **SQLite** | Local file-based store, populated from the CSV files on startup |
| Data access | `sqlite3` (standard library) | Direct, dependency-free access; sufficient for a read-only app |
| CSV parsing | `csv` (standard library) | Reads the Letterboxd exports from `Datadir` |
| Dependency management & runner | **uv** | Manages the virtual environment, dependencies, and runs the app |

### Running the application

Dependencies and execution are managed with **uv**. Typical commands:

- Install dependencies: `uv sync`
- Run the development server: `uv run flask run`

### Rationale

- **Server-rendered HTML** (Flask + Jinja2) keeps the app simple and JavaScript-free.
- **HTMX** provides interactive sorting and search by swapping HTML fragments returned
  from the server, avoiding any front-end build step or SPA framework.
- **SQLite** matches the read-only, single-user nature of the app and needs no
  separate database server on the Linux host.
- **uv** gives fast, reproducible dependency management and a single tool for
  environment setup and running.

