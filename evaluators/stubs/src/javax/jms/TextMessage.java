package javax.jms;

// Stub interface for JMS TextMessage
public interface TextMessage extends Message {
    String getText() throws JMSException;
    void setText(String text) throws JMSException;
}
