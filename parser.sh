#!/usr/bin/env bash

set -euo pipefail

LOG_FILE="access.log"

init_context(){
    if [[ ! -f "$LOG_FILE" ]]; then
        echo "$LOG_FILE отсутствует. Переместите файл access.log в текущую директорию."
        return 1 
    fi
}

date_filter(){
    local TARGET_DATE="$1"
    if [[ ! $TARGET_DATE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        echo "Некорректный формат даты. Используйте YYYY-mm-dd."
        return 1
    fi

    if ! date=$(date -d "$TARGET_DATE" "+%d/%b/%Y" 2>/dev/null);then
        echo "Некорректная дата."
        return 1
    fi

    if [[ -s "${TARGET_DATE}_access.log" ]]; then
        echo "Файл лога за выбранную дату уже существует. Переименуйте или переместите файл и повторите попытку."
        echo "Файл лога не был создан"
        return 1
    fi

    records_counter=$(awk -v date="$date" ' $4 ~ date {
     if (NF < 9) next;
     counter ++ 
     } 
     END {
     print counter + 0
     }' access.log )
    if [[ "$records_counter" -eq 0 ]]; then
        echo "Логи по выбранной дате не найдены."
        return 1
    else
        printf "=== Фильтр по дате $date ===\n"
        printf "Найдено записей за указанную дату: $records_counter\n"
        awk -v date="$date" '
        $4 ~ date {
            if (NF < 9) next;
            print
        }
        ' access.log > "${TARGET_DATE}_access.log"
    fi
}


error_status_code(){
    init_context

    awk '{
        if (NF < 9) next;
        status_code=$9
    }
    
    status_code >= 400 && status_code < 600 {
            print
    }
    ' $LOG_FILE > errors.log 

    error_count=$(wc -l < errors.log)
    printf "=== Найденные ошибки === \nСтроки с ошибками помещены в errors.log (${error_count} записей)\n\n"
}

top_ips(){
    printf "=== Топ 3 активных IP адресов ===\n\n"
    awk '{ if (NF < 9) next; print $1 }' $LOG_FILE | sort | uniq -c | sort -rn | head -3 | \
    awk '{ print $2 ": " $1 " requests"}'
}


methods_counter(){
    printf "=== Статистика по методам ===\n\n"
        awk '{ if (NF < 9) next; print $6 }' $LOG_FILE | sed 's/"//' | sort | uniq -c | sort -rn | \
        awk '{ print $2 ": " $1 }'
}



main(){
    if [[ "${1:-}" == --date=* ]]; then
        TARGET_DATE="${1#--date=}"
        init_context
        date_filter "$TARGET_DATE"
        LOG_FILE="${TARGET_DATE}_access.log"
        top_ips
        methods_counter
        error_status_code
        rm -f "$LOG_FILE"
    else
        init_context || exit 1
        top_ips
        methods_counter
        error_status_code
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi