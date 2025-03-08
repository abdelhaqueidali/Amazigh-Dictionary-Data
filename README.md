# Amazigh Language Databases (IRCAM DGLAI and Others)

**[Download All Databases](https://github.com/abdelhaqueidali/Amazigh-Dictionary-Data/archive/refs/heads/main.zip)**

This repository contains SQLite database files (`.db`) intended for use with Amazigh language applications, particularly those involving dictionaries, spell-checking, and word prediction. The primary data source is the **IRCAM DGLAI** database, with other supplementary databases also included.

*   **IRCAM (l'Institut Royal de la Culture Amazighe):** A leading institution for Amazigh language and culture. Data from IRCAM, specifically the *Dictionnaire Général de la Langue Amazighe Informatisé (DGLAI)*, represents a standardized and authoritative source for Amazigh vocabulary and orthography.

**Database Files:**

The `.db` files contain tables with words with other languages translation, mainly Amazigh, Arabic and French. Here's a breakdown:

*    `dglai14.db`:  The core IRCAM DGLAI data. This is the primary dictionary database.
*    -`Amsfti.db`: The core Ircam conjugation data from its Amsfti data. This tool may be helpful for creating an extended version to cover missing verbs: [Amazigh Conjugator](https://github.com/abdelhaqueidali/Amazigh-Conjugator).
*   `eng.db`: An English dictionary not reliable as it is likely made via automated translation tool from the DGLAi file.
*    `msmun_ar.db`: Msmun Awal Arabic data, a reliable dictionary which has data from an old DGLAi version with additional enteries that are not yet in the new DGLAi file.
*    `msmun_fr.db`: Msmun Awal French data, The same as the previous one but with French.
*   `tawalt.db`: Amazigh - Arabic Data sourced from Madghis U'Madi dictionary.
*    `tawalt_fr.db`: Amazigh - French version of Madghis' dictionary.

**Usage:**

These database files can be used in a variety of applications:

1.  **Mobile Keyboard Apps:** They are *primarily intended* for integration into mobile keyboard applications that support custom dictionaries and word prediction. The `.db` files can be used to provide:
    *   **Word Prediction:** Suggest words as the user types.
    *   **Spell Checking:** Identify and correct misspelled words.
    *   **Autocompletion:** Complete words based on partial input.
    *   **Dictionary Lookup:** Allow users to search for word definitions.

2.  **Language Learning Apps:** The databases can be incorporated into apps designed for learning Amazigh, providing a vocabulary resource for learners.

3.  **Linguistic Research:** Researchers can use the data for analyzing Amazigh vocabulary.

4.  **Natural Language Processing (NLP):** The data can be used for training NLP models for tasks like machine translation, text analysis, and speech recognition. the DGLAi data is suitable as it has its words categorized.

**How to Use (General Guidelines):**

The specific method for using these `.db` files will depend on the target application.

*   **Other Applications:** If you're developing your own application, you'll need to use an SQLite library (available for most programming languages) to connect to and query the database. Common SQL queries would include:
    *   `SELECT word FROM words WHERE word LIKE 'prefix%'` (for word prediction)
    *   `SELECT definition FROM words WHERE word = 'searchTerm'` (for dictionary lookup)

* **Direct access with SQLite browser:** For research, you can directly examine the files contents using DB Browser for SQLite, available for free.

**Important Considerations:**

*   **Character Encoding:** Ensure that your application correctly handles Unicode characters, especially the Tifinagh script.
*   **Database Schema:** The exact structure of the tables within each `.db` file may vary. You might need to examine the database schema (using an SQLite browser like DB Browser for SQLite) to understand the available fields and relationships.
*   **Data Licensing:** While the data is provided here, be aware of any licensing restrictions associated with the original sources (IRCAM, Tawalt, etc.).  Check the IRCAM website for their terms of use.
*	**Different scripts**: Some databases use Tifinagh script with Latin, some have Arabic script.

This repository provides a valuable resource for developers and researchers working with the Amazigh language, centered around the authoritative IRCAM DGLAI dictionary. By leveraging these databases, you can create more powerful and user-friendly Amazigh language tools.
