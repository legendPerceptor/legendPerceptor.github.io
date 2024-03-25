---
title: A Guide to WebCheckout for FE Tech Directors
author: yuanjian
date: 2024-03-24 09:34:00 -0500
categories: [Tutorial]
tags: [WebCheckout, Fire Escape Films, Tech Director]
pin: true
---

I am glad that you decide to learn the tech management behind Fire Escape Films. We are a registered student organization (RSO) at the University of Chicago. Feel free to check [our website](https://www.fireescapefilms.org) for more information. The purpose of this tutorial is to onboard new tech directors and relieve them from the pain of reading WebCheckout's official documentation. Nonetheless, always refer to the [official documentation](https://community.webcheckout.net/login/?redirect_to=https%3A%2F%2Fcommunity.webcheckout.net%2FFind_Resources%2F) for anything that is not covered here. You need to register an account to access the documentation. Please identify yourself during the process and some reviewers will process your request.


## 1. Gear Hiearchy 

To start with, we need to know where to find gears and understand what the **Gear Hiearchy** is. Let's navigate to the `Resources` menu and take a look at our gears. The names of all our gears start with `LMC FE`. So it is an easy way to search with this term included. There are `Resource` and `Type`, which may look confusing for you. Our rule is that a `Resource` **uniquely** refers to a specific item, and there will be only one such physical item. A `Type` can contain multiple devices of the same type, for instance, we have multiple boom poles, but they are all under the `LMC FE Boom Poles` type. 

![Find Resources](https://i.ibb.co/282h9dz/FE-Search-Resources.png)
_Figure 1. The "Resources" menu is where you look for cameras, lights, audio gears, camera supports, etc._

The gear hiearchy helps us locate all our gears under one category `LMC Fire Escape`, and each gear is under some subcategory (there can be multiple levels of subcategories). To illustrate the hiearchy, we can use a tree as shown in **Figure 2**. We always ask students to reserve gears on a `Type` instead of on a `Resource` because it is meaningless and troublesome to figure out which "LMC FE Boom Pole" they reserved.

![Gear Hiearchy Tree](https://i.ibb.co/VYjyqnP/Gear-Hiearchy.png)
_Figure 2. The "Gear Hiearchy" illustration._

On the WebCheckout backend, the hiearchy tree can be navigated by `Parent Type` and `Subtypes`. The `Parent Type` helps you navigate closer to the root, while the `Subtypes` navigates you further down to the leaf. Each blue text shown in **Figure 3** is clickable. Combining the Resource search and the navigation, you should be able to find every single gear we have in the system.

![Parent Types and Subtypes](https://i.ibb.co/vkbctkd/parent-subtypes.png)
_Figure 3. Navigate through the hiearchy on the backend._

## 2. Authorizations

All of our gears are under Fire Escape authorizations, so other groups by default have no access to our equipment. The basic authorization is called `Fire Escape: General Access`. Some other more advanced gears are under their special access. The existing authorizations are shown in **Figure 4**. A common request from students would be to add them into some specific authorization group to obtain access for some gears.

![Authorization](https://i.ibb.co/7tcdLNb/FE-Authorizations.png)
_Figure 4. Fire Escape Films Existing Authorizations._

There is also a little hiearchy in the authorization, which may look confusing at the first glance. I'll explain it breifly here. We have an `Authorization Set` to begin with, then there is an `Authorization Group`, and finally it is the `Sections` for each authorization group. The `Authorization Set` is where all our equipment sits in. It serves as a super set that distinguishes our authorization and some other organization's authorization. The `Authorization Group` adds another layer of protection to the gears--- it contains a subset of the gears and only the users who are in the group can access those gears. The `Sections` manages the expiration of the authorization. Usually we update the sections annually to remove old users from the authorization. Therefore, students who have access before may suddenly find that they no longer have access and ask for reauthorization. We usually collect all students' information at the first general meeting in the Fall Quarter and add them into the section for that academic year.

### 2.1 Add Students to An Authorization

**Figure 5** shows how you can add a student to an authorization. Remember to go to the `Section` to add people. You should see a similar page for other authorization groups. After typing in their name, press `Enter`, and the website will ask you to verify your pin, then the student will be granted access. 

![Add students to an authorization](https://i.ibb.co/qnx9mjT/FE-Add-Member-Into-Authorization.png)
_Figure 5. Add people to an authorization section_

### 2.2 Add Gears to An Authorization

We always add a `Resource Type` to the authorization instead of the individual resources. I'd like to use a forward reference to **Figure 14** to give you an idea on how to add authorizations to a gear. We navigate to the `Authorizations` menu and ensure we check the `Requires Authorization` checkbox. Most gears should be under `General Access`. For special access groups, find the corresponding name and put it in the text field.

## 3. Reserve Gears for Other People

As tech directors, we have the capability to reserve gears for another student. We can also use the same method to reserve gears for ourselves. If you feel more comfortable using the backend to reserve gears, it means something can be improved. I encourge everyone to use the Patron Portal to checkout gears. If you find something inconvenient in that way, improve it with your tech director power. Nonetheless, there are some gears that we intentionally make them not visible in the Patron Portal. Some good examples are the `FE Photo Backdrop`, `FE Archive Drive`, etc. To reserve these gears, we should use the backend.

To make a reservation, in other words, make a new allocation, click the tent button, as shown in **Figure 6**. The first step is to choose the right `Patron`, that is the person to be responsible for the reservation. Select the `Start` and `End` time, **ignore** `Barcodes`, and click the `Continue` button.

![Make a new allocation](https://i.ibb.co/QczGQzW/Reserve-Gears-For-People.png)
_Figure 6. Make a New Reservation (Allocation)_


After that, you will see an interface as shown in **Figure 7**. You should have a clear mind of the **Gear Hierachy** to find the gears. Let's add the Sony A7S3 bundle. After double-clicking the `Add LMC FE Sony A7SIII Bundle bundle`, 6 items will be added to the checkout, as the bundle contains 6 items. You can continue adding more gears. After everything looks correct, click `Confirm Reservation`. An email will be sent to the student and they can show up at the Cage to pick equipment up.

![Reserve Gears](https://i.ibb.co/cwKPD2g/Reserve-Gears.png)
_Figure 7. Select Gears for Reservation._

For an existing allocation, we can modify its properties. The easiest way to find an allocation is through the person's name. In the `People` menu, we can search by name, as shown in **Figure 8**.

![Find Luke's Reservation](https://i.ibb.co/bRf2PP8/Luke-Reservation-Modification.png)
_Figure 8. Find an existing allocation by people's name._ 

We can click the `Edit Reservation` button to change items in the reservation, change the start/end time. We can even change the end time for a checked out allocation. Don't abuse this functionality because we hope people to return gears in no more than 3 days.

![Modify Luke's Reservation](https://i.ibb.co/2KNmNvp/Edit-Reservation.png)
_Figure 9. Edit Luke's Reservation._

## 4. Add New Gears to The System

We have different steps for adding another copy for the existing gears and adding a complete new equipment. To determine whether the gear exists, you can search for the resource type first. Sometimes the names may be different from what you think, so try searching more thoroughly. 

### 4.1 Add non-existing gears

If the gear does not exist, we need to create a new `Resource Type` for it. The important part is to make sure it has a proper parent type. For example, in **Figure 10**, we want to add a new Boom Arm, which we never had one before. The parent type should be `LMC FE Lighting`. We want every type of resource to require authorization.

![Add new resource type](https://i.ibb.co/H48w313/FE-New-Resource-Type.png)
_Figure 10. Add a new resource type._

Then we need to add an actual resource to the type. We can go to "Resources->New Equipment" to open up a window as shown in **Figure 11**. As we just created a `Type`, the `Type` should autocomplete itself after typing in the first a few characters. Moreover, we need to set the barcode for this resource to complete creation--- you can also add the barcode later, but don't forget to add it!

> Note that there is a bug in the Web Checkout system: when you delete a resource, the barcode and resource id will remain in the database, causing you not able to create another resource with the same resource id or barcode. So **do not delete a resource**, or make sure the resource ID and barcode fields are cleared before deletion, otherwise you will need a new barcode!
{: .prompt-danger }

![Add new resource](https://i.ibb.co/3MPwX1K/FE-New-Resource.png)
_Figure 11. Add a new resource._

Then we need to add an attachment for the resource type. This attachment serves as a thumbnail in the Patron Portal. This step was ignored by some previous tech directors resulting in no images for some gears. Please avoid forgetting this step. To add an attachment, navigate to the resource type and click the attachment button to open up the following window shown in **Figure 12**. To get the image, I usually go to [B&H](https://www.bhphotovideo.com/) to get a photo of the product. Make sure the attachment's visibility is set to public.

![Add attachment](https://i.ibb.co/HVDYk4w/Boom-Arm-picture.png)
_Figure 12. Add an attachment for the resource type._

Next, put the image URL for the attachment into the `Image URL` text field in the `Admin` menu for the resource type. If you didn't find the attachment button, it is captured in **Figure 13**, which is to the right of the highlighted `Admin` menu. Now it shows a number 1, indicating there is an attachment there.

![Finished adding boom-arm](https://i.ibb.co/sH8hwHp/Finished-Adding-Boom-Arm.png)
_Figure 13. The interface should look like this when you finish adding an image_

Then we need to add authorization to the equipment. Go to `Authorizations` menu, and add the resource type to the proper authorization set. The Boom Arm should go to the General Access, and therefore this section should look like **Figure 14**.

![Adding Authorization](https://i.ibb.co/fkKBpb9/Add-Authorization-Boom-Arm.png)
_Figure 14. Add authorization to the Boom Arm._

It always helps to go to the Patron Portal to verify if the gear is added there and everything looks correct to you. As shown in **Figure 15**, we can see that the `LMC FE Mid-range Boom Arm` shows up in the `LMC FE Lighting`.

![Patron Portal Verification](https://i.ibb.co/J7YWvfg/Patron-portal-Boom-Arm.png)
_Figure 15. Patron Portal Verification._

### 4.2 Add a copy of an existing gear.

There can be fewer steps to add a copy of an existing device. The WebCheckout provides a `duplicate this resource` option under the `Admin` menu for a resource, as shown in **Figure 16**. We just need to change the resource id to a new one, usually just making (001) to (002), etc. And we should add a barcode after this operation. Then the new equipment is ready to go. Much simpler, isn't it?

![Duplicate a light stick](https://i.ibb.co/ZTTL0jP/Duplicate-dialog.png)
_Figure 16. Duplicate an existing resource._

This method is more of a shortcut, you can always follow the steps mentioned in 4.1 to add a new resource.


## 5. Create A Bundle for Gears with Multiple Parts

For a more complicated gear, we put multiple parts into a bundle for easier reservation. We also try our best to put them physically in the same bag or at least close to each other. For example, the new Amaron light has several parts as shown in **Figure 17**. We create a new resource type called `LMC FE Amaron Light` for the light to show up under `LMC FE Lighting`. Inside the new resource type, we create a new type for each part of the gear. We can add individual resources to the types as usual. But here we make them invisible in Patron Portal--- Go to the `Admin` menu, there will be a checkbox for visibility in the Patron Portal, just uncheck that. We create another resource type called "XXX Bundle". We don't add any actual resources into it but go to the `Bundle` menu to associate each of the other types with the bundle resource type, as shown in **Figure 18**.

![Bundle Idea Illustration](https://i.ibb.co/dLFf6K2/Bundle-Light.png)
_Figure 17. Amaron Light Bundle Illustration._

![Bundle other resources](https://i.ibb.co/brRS4Yh/Bundle-Resources.png)
_Figure 18. Add Resources Into The Bundle._

In this way, when a student reserves the bundle, the system will help add all the actual resources inside the bundle to the checkout.