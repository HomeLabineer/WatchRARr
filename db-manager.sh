#!/bin/bash

# ------------------------------
# WatchRARr DB Manager Info
# ------------------------------
# Copyright (C) 2023 HomeLabineer
# This project is licensed under the MIT License. See the LICENSE file for details.
# Script Name: db-manager.sh
# Description: A script to recursively watch a directory for RAR files and extract them upon creation.
#              The script processes both single RAR files and split/spanned RAR archives. It also maintains
#              a SQLite database to keep track of processed files and avoid reprocessing them.

#
# Usage:
#   1. Replace <your_db_file> in the script with the path to your SQLite database file.
#   2. Save the script as db_manager.sh
#   3. Make the script executable: chmod +x db_manager.sh
#   4. Run the script: ./db_manager.sh
#   5. Follow the interactive menu prompts to perform the desired actions.

DB_FILE="db/extracted-files.db"

function add_entry() {
    read -p "Enter the file path to add: " filepath
    mtime=$(date +%s)
    sqlite3 "$DB_FILE" "INSERT INTO processed_files (filepath, mtime) VALUES ('$filepath', '$mtime');" 2>/tmp/error.log
    if [ $? -eq 0 ]; then
        echo "Successfully added the file path to the database."
    else
        echo "Error adding the file path:"
        cat /tmp/error.log
    fi
}

function remove_entry() {
    read -p "Enter the file path to remove: " filepath
    sqlite3 "$DB_FILE" "DELETE FROM processed_files WHERE filepath='$filepath';" 2>/tmp/error.log
    if [ $? -eq 0 ]; then
        echo "Successfully removed the file path from the database."
    else
        echo "Error removing the file path:"
        cat /tmp/error.log
    fi
}

function search_entry() {
    read -p "Enter a keyword to search: " keyword
    echo "Searching for entries containing '$keyword':"
    sqlite3 "$DB_FILE" "SELECT filepath FROM processed_files WHERE filepath LIKE '%$keyword%';" 2>/tmp/error.log
    if [ $? -ne 0 ]; then
        echo "Error searching entries:"
        cat /tmp/error.log
    fi
}

function show_all_entries() {
    echo "Showing all entries in the database:"
    sqlite3 "$DB_FILE" "SELECT filepath FROM processed_files;" 2>/tmp/error.log
    if [ $? -ne 0 ]; then
        echo "Error showing all entries:"
        cat /tmp/error.log
    fi
}

function backup_database() {
    DB_DIR=$(dirname "$DB_FILE")
    DB_NAME=$(basename "$DB_FILE" .db)
    TIMESTAMP=$(date +%Y%m%d%H%M%S)

    echo "Select backup file naming:"
    echo "1. Default naming"
    echo "2. Custom naming"
    read -p "Enter the option number: " naming_option

    case $naming_option in
        1)
            BACKUP_FILE="${DB_DIR}/${DB_NAME}_${TIMESTAMP}.bak"
            ;;
        2)
            read -p "Enter the custom backup file name (without extension): " custom_name
            custom_name=${custom_name:0:25}  # Truncate the input to a maximum of 25 characters
            BACKUP_FILE="${DB_DIR}/${custom_name}_${TIMESTAMP}.bak"
            ;;
        *)
            echo "Invalid option. Aborting backup."
            return
            ;;
    esac

    cp "$DB_FILE" "$BACKUP_FILE" 2>/tmp/error.log
    if [ $? -eq 0 ]; then
        echo "Successfully backed up the database to $BACKUP_FILE."
    else
        echo "Error backing up the database:"
        cat /tmp/error.log
    fi
}

function restore_database() {
    DB_DIR=$(dirname "$DB_FILE")
    DB_NAME=$(basename "$DB_FILE" .db)

    echo "Available backups:"
    i=1
    for f in "${DB_DIR}"/*.bak; do
        size=$(du -sh "$f" | awk '{print $1}')
        mtime=$(date -r "$f" '+%Y-%m-%d %H:%M:%S')
        echo "${i}. ${f} (Size: ${size}, Created: ${mtime})"
        BACKUP_FILES[i]=$f
        i=$((i+1))
    done

    read -p "Enter the number of the backup to restore: " backup_choice
    BACKUP_FILE=${BACKUP_FILES[$backup_choice]}

    if [ -z "$BACKUP_FILE" ]; then
        echo "Invalid choice. Aborting restore."
        return
    fi

    # Check if the backup file is a valid SQLite database
    FILE_SIGNATURE=$(xxd -l 16 -p "$BACKUP_FILE")
    SQLITE_SIGNATURE="53514c69746520666f726d6174203300"

    if [ "$FILE_SIGNATURE" != "$SQLITE_SIGNATURE" ]; then
        echo "The selected file is not a valid SQLite database. Aborting restore."
        return
    fi

    read -p "Are you sure you want to restore the selected backup? This will overwrite the current database [y/N]: " confirm_restore
    if [[ ! $confirm_restore =~ ^[Yy]$ ]]; then
        echo "Restore operation cancelled."
        return
    fi

    cp "$BACKUP_FILE" "$DB_FILE" 2>/tmp/error.log
    if [ $? -eq 0 ]; then
        echo "Successfully restored the database from $BACKUP_FILE."
    else
        echo "Error restoring the database:"
        cat /tmp/error.log
    fi
}

function delete_backup() {
    list_backups
    read -p "Enter the number of the backup to delete: " backup_choice
    BACKUP_FILE=${BACKUP_FILES[$backup_choice]}

    if [ -z "$BACKUP_FILE" ]; then
        echo "Invalid choice. Aborting delete."
        return
    fi

    read -p "Are you sure you want to delete the selected backup? This action cannot be undone [y/N]: " confirm_delete
    if [[ ! $confirm_delete =~ ^[Yy]$ ]]; then
        echo "Delete operation cancelled."
        return
    fi

    rm "$BACKUP_FILE" 2>/tmp/error.log
    if [ $? -eq 0 ]; then
        echo "Successfully deleted the backup: $BACKUP_FILE."
    else
        echo "Error deleting the backup:"
        cat /tmp/error.log
    fi
}

function list_backups() {
    DB_DIR=$(dirname "$DB_FILE")
    DB_NAME=$(basename "$DB_FILE" .db)

    echo "Available backups:"
    i=1
    for f in "${DB_DIR}"/*.bak; do
        size=$(du -sh "$f" | awk '{print $1}')
        mtime=$(date -r "$f" '+%Y-%m-%d %H:%M:%S')
        echo "${i}. ${f} (Size: ${size}, Created: ${mtime})"
        BACKUP_FILES["$i"]=$f
        i=$((i+1))
    done
}

function show_main_help() {
    echo "Main menu help:"
    echo "1. Add entry: Add a file path to the database."
    echo "2. Remove entry: Remove a file path from the database. (Be exact, try copy/pasta from results of '3. Search entry')"
    echo "3. Search entry: Fuzzy search for entries containing a specific keyword or part of a file name."
    echo "4. Show all entries: Display all file paths in the database."
    echo "5. Advanced Menu: Access advanced options such as database backup and restore."
    echo "6. Help: Display this help message."
    echo "7. Quit: Exit the script."
}

function show_advanced_help() {
    echo "Advanced menu help:"
    echo "1. Backup Menu: Manage your DB backups."
    echo "2. Back: Return to the main menu."
    echo "3. Help: Display this help message."
    echo "4. Quit: Exit the script."
}

function show_backup_help() {
    echo "Backup menu help:"
    echo "1. Backup database: Create a backup of the database with either default or custom naming."
    echo "2. Restore database: Restore the database from a previously created backup."
    echo "3. Delete backup: Delete a backup file by providing its exact name and full path (e.g., db/extracted-files_date.bak)."
    echo "4. List backups: List all available backup files."
    echo "5. Back: Return to the Advanced menu."
    echo "6. Help: Display this help message."
    echo "7. Quit: Exit the script."
}

function advanced_menu() {
    while true; do
        echo "Advanced menu:"
        echo "1. Backup menu"
        echo "2. Back"
        echo "3. Help"
        echo "4. Quit"
        read -p "Enter the action number: " action

        case $action in
            1)
                backup_menu
                ;;
            2)
                break
                ;;
            3)
                show_advanced_help
                ;;
            4)
                exit 0
                ;;
            *)
                echo "Invalid action. Please enter a number between 1 and 4."
                ;;
        esac
        echo
    done
}

function backup_menu() {
    while true; do
        echo "Backup menu:"
        echo "1. Backup database"
        echo "2. Restore database"
        echo "3. Delete backup"
        echo "4. List backups"
        echo "5. Back"
        echo "6. Help"
        echo "7. Quit"
        read -p "Enter the action number: " action

        case $action in
            1)
                backup_database
                ;;
            2)
                restore_database
                ;;
            3)
                delete_backup
                ;;
            4)
                list_backups
                ;;
            5)
                break
                ;;
            6)
                show_backup_help
                ;;
            7)
                exit 0
                ;;
            *)
                echo "Invalid action. Please enter a number between 1 and 7."
                ;;
        esac
        echo
    done
}

while true; do
    echo "Select an action:"
    echo "1. Add entry"
    echo "2. Remove entry"
    echo "3. Search entry"
    echo "4. Show all entries"
    echo "5. Advanced Menu"
    echo "6. Help"
    echo "7. Quit"
    read -p "Enter the action number: " action

    case $action in
        1)
            add_entry
            ;;
        2)
            remove_entry
            ;;
        3)
            search_entry
            ;;
        4)
            show_all_entries
            ;;
        5)
            advanced_menu
            ;;
        6)
            show_main_help
            ;;
        7)
            break
            ;;
        *)
            echo "Invalid action. Please enter a number between 1 and 7."
            ;;
    esac
    echo
done