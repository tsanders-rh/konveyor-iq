package org.eclipse.microprofile.reactive.messaging;

import java.lang.annotation.*;

@Target({ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
public @interface Incoming {
    String value();
}
