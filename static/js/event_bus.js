"use strict";


class EventBus {

    constructor() {
        this.events = {};
    }


    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }

        this.events[event].push(callback);
    }


    emit(event, payload = {}) {

        if (!this.events[event]) {
            return;
        }

        this.events[event].forEach(callback => {
            try {
                callback(payload);
            }
            catch(error) {
                console.error(
                    "EventBus error:",
                    event,
                    error
                );
            }
        });
    }

}


window.DIP_EVENT_BUS = new EventBus();