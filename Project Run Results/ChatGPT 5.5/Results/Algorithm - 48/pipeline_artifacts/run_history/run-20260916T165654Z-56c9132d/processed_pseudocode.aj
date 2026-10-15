    INPUT Folder
    INPUT FileType

    FUNCTION Search(CurrentFolder)
        FOR EACH Item IN CurrentFolder
            IF Item is a file AND Item.Type = FileType THEN
                OUTPUT Item
            ELSE IF Item is a folder THEN
                Search(Item)
            ENDIF
        ENDFOR
    END FUNCTION

    Search(Folder)
END