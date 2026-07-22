#!/bin/bash

OUTPUT="sapientia_phase3_context.txt"

rm -f "$OUTPUT"

echo "==========================================" >> "$OUTPUT"
echo " SAPientia Phase 3 Context" >> "$OUTPUT"
echo "==========================================" >> "$OUTPUT"
echo "" >> "$OUTPUT"

FILES=(

"src/sapientia/services/connector_lifecycle_service.py"

"src/sapientia/services/semantic_service.py"

"src/sapientia/services/knowledge_fusion_service.py"

"src/sapientia/services/enterprise_concept_service.py"

"src/sapientia/engines/semantic/semantic_engine.py"

"src/sapientia/engines/knowledge_fusion/knowledge_fusion_engine.py"

"src/sapientia/engines/enterprise_concept/enterprise_concept_engine.py"

"src/sapientia/repositories/dataset_repository.py"

"src/sapientia/repositories/dataset_context_repository.py"

"src/sapientia/repositories/semantic_repository.py"

"src/sapientia/repositories/knowledge_repository.py"

"src/sapientia/repositories/enterprise_concept_repository.py"

"src/sapientia/models"

"src/sapientia/database"

)

for ITEM in "${FILES[@]}"
do

    if [ -d "$ITEM" ]; then

        echo "" >> "$OUTPUT"
        echo "#########################################################" >> "$OUTPUT"
        echo "DIRECTORY: $ITEM" >> "$OUTPUT"
        echo "#########################################################" >> "$OUTPUT"

        find "$ITEM" -name "*.py" | while read FILE
        do

            echo "" >> "$OUTPUT"
            echo "=========================================================" >> "$OUTPUT"
            echo "$FILE" >> "$OUTPUT"
            echo "=========================================================" >> "$OUTPUT"

            cat "$FILE" >> "$OUTPUT"

            echo "" >> "$OUTPUT"

        done

    elif [ -f "$ITEM" ]; then

        echo "" >> "$OUTPUT"
        echo "=========================================================" >> "$OUTPUT"
        echo "$ITEM" >> "$OUTPUT"
        echo "=========================================================" >> "$OUTPUT"

        cat "$ITEM" >> "$OUTPUT"

        echo "" >> "$OUTPUT"

    else

        echo "" >> "$OUTPUT"
        echo "$ITEM  --> NOT FOUND" >> "$OUTPUT"

    fi

done

echo ""
echo "Created $OUTPUT"