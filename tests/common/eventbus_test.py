import pytest

from wwwpy.common.eventbus import EventBus


# Import the EventBus implementation


# Define test classes
class Pet:
    def __init__(self, name="Generic"):
        self.name = name


class Dog(Pet):
    def bark(self):
        return "Woof!"


class Cat(Pet):
    def meow(self):
        return "Meow!"


class Hamster(Pet):
    def squeak(self):
        return "Squeak!"


# Tests
class TestEventBus:

    def test_basic_subscribe_publish(self):
        """Test basic subscription and publishing works."""
        bus = EventBus()
        events_received = []

        def handler(pet: Pet):
            events_received.append(pet)

        sub = bus.subscribe(handler)

        pet = Pet("Generic")
        bus.publish(pet)

        assert len(events_received) == 1
        assert events_received[0] is pet

    def test_type_specific_subscribe(self):
        """Test that subscriptions are type-specific."""
        bus = EventBus()
        pets_received = []
        dogs_received = []
        cats_received = []

        def pet_handler(pet: Pet):
            pets_received.append(pet)

        def dog_handler(dog: Dog):
            dogs_received.append(dog)

        def cat_handler(cat: Cat):
            cats_received.append(cat)

        bus.subscribe(pet_handler)
        bus.subscribe(dog_handler)
        bus.subscribe(cat_handler)

        pet = Pet("Generic")
        dog = Dog("Buddy")
        cat = Cat("Whiskers")

        bus.publish(pet)
        assert len(pets_received) == 1
        assert len(dogs_received) == 0
        assert len(cats_received) == 0

        bus.publish(dog)
        assert len(pets_received) == 1  # The dog isn't delivered to pet_handler!
        assert len(dogs_received) == 1
        assert len(cats_received) == 0

        bus.publish(cat)
        assert len(pets_received) == 1  # The cat isn't delivered to pet_handler!
        assert len(dogs_received) == 1
        assert len(cats_received) == 1

    def test_publish_with_explicit_type(self):
        """Test publishing with an explicit 'on' type parameter."""
        bus = EventBus()
        pets_received = []
        dogs_received = []
        cats_received = []

        def pet_handler(pet: Pet):
            pets_received.append(pet)

        def dog_handler(dog: Dog):
            dogs_received.append(dog)

        def cat_handler(cat: Cat):
            cats_received.append(cat)

        bus.subscribe(pet_handler, on=Pet)
        bus.subscribe(dog_handler, on=Dog)
        bus.subscribe(cat_handler, on=Cat)

        dog = Dog("Buddy")

        # Publish dog as Pet - should be received by pet_handler
        bus.publish(dog, on=Pet)
        assert len(pets_received) == 1
        assert len(dogs_received) == 0  # Important! We published as Pet, not Dog
        assert len(cats_received) == 0

        # Publish dog as Dog - should be received by dog_handler
        bus.publish(dog, on=Dog)
        assert len(pets_received) == 1  # No change here
        assert len(dogs_received) == 1
        assert len(cats_received) == 0

    def test_unsubscribe(self):
        """Test that unsubscribing works."""
        bus = EventBus()
        received = []

        def handler(pet: Pet):
            received.append(pet)

        subscription = bus.subscribe(handler)

        pet = Pet("Generic")
        bus.publish(pet)
        assert len(received) == 1

        # Unsubscribe
        result = subscription.unsubscribe()
        assert result is True

        bus.publish(pet)
        assert len(received) == 1  # Count should not increase

        # Unsubscribing again should return False
        result = subscription.unsubscribe()
        assert result is False

    def test_type_inference(self):
        """Test type inference from function annotations."""
        bus = EventBus()
        dog_received = None
        cat_received = None

        def dog_handler(dog: Dog):
            nonlocal dog_received
            dog_received = dog

        def cat_handler(cat: Cat):
            nonlocal cat_received
            cat_received = cat

        # No explicit type, should infer from annotations
        bus.subscribe(dog_handler)
        bus.subscribe(cat_handler)

        dog = Dog("Rex")
        cat = Cat("Felix")

        bus.publish(dog)
        assert dog_received is dog
        assert cat_received is None

        bus.publish(cat)
        assert cat_received is cat

    def test_missing_type_inference(self):
        """Test error when type cannot be inferred."""
        bus = EventBus()

        def handler_no_annotation(obj):
            pass

        with pytest.raises(ValueError):
            bus.subscribe(handler_no_annotation)

    def test_multiple_subscribers_same_type(self):
        """Test multiple subscribers for the same type."""
        bus = EventBus()
        count1 = 0
        count2 = 0

        def handler1(pet: Pet):
            nonlocal count1
            count1 += 1

        def handler2(pet: Pet):
            nonlocal count2
            count2 += 1

        bus.subscribe(handler1)
        bus.subscribe(handler2)

        pet = Pet()
        bus.publish(pet)

        assert count1 == 1
        assert count2 == 1

    def test_subscription_is_active(self):
        """Test the is_active property of Subscription."""
        bus = EventBus()

        def handler(pet: Pet):
            pass

        subscription = bus.subscribe(handler)
        assert subscription.is_active is True

        subscription.unsubscribe()
        assert subscription.is_active is False

    def test_decorator_syntax(self):
        """Test using subscribe as a decorator."""
        bus = EventBus()
        received = []

        @bus.subscribe
        def handler(pet: Pet):
            received.append(pet)

        pet = Pet()
        bus.publish(pet)

        assert len(received) == 1
        assert received[0] is pet

    def test_subscriber_count(self):
        """Test get_subscriber_count method."""
        bus = EventBus()

        def handler1(pet: Pet): pass

        def handler2(pet: Pet): pass

        def handler3(dog: Dog): pass

        bus.subscribe(handler1)
        assert bus.get_subscriber_count(Pet) == 1

        bus.subscribe(handler2)
        assert bus.get_subscriber_count(Pet) == 2

        bus.subscribe(handler3)
        assert bus.get_subscriber_count(Dog) == 1

    def test_clear(self):
        """Test clearing all subscriptions."""
        bus = EventBus()

        def handler1(pet: Pet): pass

        def handler2(dog: Dog): pass

        bus.subscribe(handler1)
        bus.subscribe(handler2)

        assert bus.get_subscriber_count(Pet) == 1
        assert bus.get_subscriber_count(Dog) == 1

        bus.clear()

        assert bus.get_subscriber_count(Pet) == 0
        assert bus.get_subscriber_count(Dog) == 0

    def test_invalid_publish_type(self):
        """Test publishing with incompatible type."""
        bus = EventBus()
        dog = Dog()

        with pytest.raises(TypeError):
            # Cat is not compatible with Dog
            bus.publish(dog, on=Cat)

    def test_publish_return_count(self):
        """Test publish returns correct count of notified callbacks."""
        bus = EventBus()

        def handler1(pet: Pet): pass

        def handler2(pet: Pet): pass

        def handler3(dog: Dog): pass

        bus.subscribe(handler1)
        bus.subscribe(handler2)
        bus.subscribe(handler3)

        count = bus.publish(Pet())
        assert count == 2

        count = bus.publish(Dog())
        assert count == 1  # Only handler3 receives it

    def test_polymorphic_subscription(self):
        """
        Test that subscribers to a base type receive events of derived types when explicitly published on that base type.
        This verifies that:
        1. eventbus.publish(Cat(), on=Pet) is received by eventbus.subscribe(callback, on=Pet)
        2. eventbus.publish(Dog(), on=Pet) is received by the same eventbus.subscribe(callback, on=Pet)
        """
        bus = EventBus()
        received_pets = []

        def pet_handler(pet: Pet):
            received_pets.append(pet)

        # Subscribe to base type
        pet_subscription = bus.subscribe(pet_handler, on=Pet)

        # Create derived type instances
        cat = Cat("Whiskers")
        dog = Dog("Rex")

        # Publish derived types on base type
        bus.publish(cat, on=Pet)
        bus.publish(dog, on=Pet)

        # Verify all were received by the Pet subscriber
        assert len(received_pets) == 2
        assert isinstance(received_pets[0], Cat)
        assert received_pets[0].name == "Whiskers"
        assert isinstance(received_pets[1], Dog)
        assert received_pets[1].name == "Rex"

        # Now test with direct publish (should NOT be received)
        received_pets.clear()

        # Direct publishing without specifying "on" parameter
        bus.publish(cat)  # Published as Cat, not as Pet
        bus.publish(dog)  # Published as Dog, not as Pet

        # Verify none were received by Pet subscriber
        assert len(received_pets) == 0, "Direct publishing should not trigger base type subscribers"

    def test_exception_isolation(self):
        """Test that exceptions in one handler don't prevent others from being called."""
        bus = EventBus()
        called_handlers = []

        def handler1(pet: Pet):
            called_handlers.append("handler1")

        def handler2(pet: Pet):
            called_handlers.append("handler2")
            raise Exception("Intentional exception in handler2")

        def handler3(pet: Pet):
            called_handlers.append("handler3")

        bus.subscribe(handler1)
        bus.subscribe(handler2)
        bus.subscribe(handler3)

        # This should not raise an exception
        bus.publish(Pet("Test"))

        # Verify all handlers were called despite the exception in handler2
        assert "handler1" in called_handlers
        assert "handler2" in called_handlers
        assert "handler3" in called_handlers
        assert len(called_handlers) == 3
